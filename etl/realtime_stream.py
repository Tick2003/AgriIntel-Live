"""
AgriIntel Real-Time Intraday Stream Generator
===============================================
Simulates high-frequency APMC / eNAM trading desk activity.

Generates bid/ask quotes and executed trades every few seconds,
fluctuating around the daily modal price with drift influenced
by live market sentiment and weather anomalies.

Public API
----------
- start_realtime_generator(commodity, mandi)
- stop_realtime_generator()
- get_intraday_trades(commodity, mandi, limit=50)
- get_stream_status() -> dict
"""

import threading
import time
import random
import math
import sys
import os
from datetime import datetime
from typing import Optional, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Stream Generator
# ---------------------------------------------------------------------------

class IntradayStreamGenerator:
    """
    Background thread that generates simulated intraday ticks and
    writes them to the ``intraday_trades`` database table.
    """

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Runtime metrics
        self.ticks_generated: int = 0
        self.start_time: Optional[float] = None
        self.commodity: Optional[str] = None
        self.mandi: Optional[str] = None

        # Simulation parameters
        self._tick_interval = 2.5        # seconds between ticks
        self._spread_bps = 80           # bid-ask spread in basis-points
        self._volatility_scale = 0.004  # per-tick volatility (σ)
        self._drift = 0.0               # mean reversion drift
        self._last_price: Optional[float] = None

    # ----- public API -----

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, commodity: str, mandi: str) -> None:
        """Start the background generator for *commodity* at *mandi*."""
        if self.is_running:
            self.stop()

        self._stop_event.clear()
        self.commodity = commodity
        self.mandi = mandi
        self.ticks_generated = 0
        self.start_time = time.time()
        self._last_price = None

        self._thread = threading.Thread(
            target=self._run_loop, daemon=True,
            name="agriintel-realtime-stream",
        )
        self._thread.start()

    def stop(self) -> None:
        """Signal the background thread to stop and wait for it."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._thread = None

    def get_status(self) -> Dict:
        uptime = time.time() - self.start_time if self.start_time else 0
        return {
            "is_running": self.is_running,
            "commodity": self.commodity,
            "mandi": self.mandi,
            "ticks_generated": self.ticks_generated,
            "uptime_seconds": round(uptime, 1),
            "ticks_per_minute": round(self.ticks_generated / max(uptime / 60, 0.01), 1),
        }

    # ----- internal loop -----

    def _run_loop(self) -> None:
        """Main generation loop — runs inside a daemon thread."""
        import database.db_manager as dbm

        anchor_price = self._get_anchor_price(dbm)
        self._last_price = anchor_price
        sentiment_bias = self._get_sentiment_bias(dbm)
        weather_factor = self._get_weather_factor(dbm)

        # Refresh biases every ~60 ticks
        refresh_counter = 0

        while not self._stop_event.is_set():
            try:
                # Refresh external biases periodically
                refresh_counter += 1
                if refresh_counter % 60 == 0:
                    sentiment_bias = self._get_sentiment_bias(dbm)
                    weather_factor = self._get_weather_factor(dbm)

                ticks = self._generate_tick_batch(
                    anchor_price, sentiment_bias, weather_factor
                )
                for tick in ticks:
                    dbm.save_intraday_trade(tick)
                    self.ticks_generated += 1

            except Exception as e:
                # Never crash the thread — log and continue
                print(f"[RealtimeStream] tick error: {e}")

            # Jitter the sleep so ticks aren't perfectly periodic
            jitter = random.uniform(-0.5, 0.5)
            self._stop_event.wait(max(0.5, self._tick_interval + jitter))

    # ----- tick generation -----

    def _generate_tick_batch(self, anchor: float, sentiment: float,
                             weather: float) -> list:
        """Generate 1–3 ticks per cycle (bid, ask, and optionally a trade)."""
        ticks = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.") + \
                  f"{random.randint(0, 999):03d}"

        # Geometric Brownian Motion step
        drift = self._drift + sentiment * 0.001 + weather * 0.0005
        shock = random.gauss(0, self._volatility_scale)
        self._last_price = self._last_price * math.exp(drift + shock)

        # Clamp price to ±15% of anchor to prevent runaway
        lo = anchor * 0.85
        hi = anchor * 1.15
        self._last_price = max(lo, min(hi, self._last_price))

        mid_price = round(self._last_price, 2)
        half_spread = anchor * (self._spread_bps / 10000) / 2

        bid_price = round(mid_price - half_spread + random.uniform(-2, 2), 2)
        ask_price = round(mid_price + half_spread + random.uniform(-2, 2), 2)

        base_qty = random.uniform(5, 50)

        # Always generate a BID and ASK
        ticks.append({
            "timestamp": now_str,
            "commodity": self.commodity,
            "mandi": self.mandi,
            "price": bid_price,
            "quantity": round(base_qty * random.uniform(0.5, 1.5), 1),
            "trade_type": "BID",
        })
        ticks.append({
            "timestamp": now_str,
            "commodity": self.commodity,
            "mandi": self.mandi,
            "price": ask_price,
            "quantity": round(base_qty * random.uniform(0.5, 1.5), 1),
            "trade_type": "ASK",
        })

        # ~60% chance of a completed TRADE each cycle
        if random.random() < 0.60:
            trade_price = round(
                random.uniform(bid_price, ask_price), 2
            )
            ticks.append({
                "timestamp": now_str,
                "commodity": self.commodity,
                "mandi": self.mandi,
                "price": trade_price,
                "quantity": round(base_qty * random.uniform(0.8, 1.2), 1),
                "trade_type": "TRADE",
            })

        return ticks

    # ----- helpers -----

    def _get_anchor_price(self, dbm) -> float:
        """Fetch the latest daily modal price as the simulation anchor."""
        try:
            df = dbm.get_latest_prices(commodity=self.commodity)
            if not df.empty:
                filtered = df[df["mandi"] == self.mandi]
                if not filtered.empty:
                    return float(filtered["price_modal"].iloc[-1])
                return float(df["price_modal"].iloc[-1])
        except Exception:
            pass
        # Fallback
        return random.uniform(1500, 4500)

    @staticmethod
    def _get_sentiment_bias(dbm) -> float:
        """
        Derive a sentiment drift from news_alerts table.
        Positive sentiment → upward drift, negative → downward.
        Range: roughly –1.0 to +1.0
        """
        try:
            news_df = dbm.get_latest_news()
            if not news_df.empty and "sentiment" in news_df.columns:
                sent_map = {"Positive": 1, "Negative": -1, "Neutral": 0}
                scores = news_df["sentiment"].map(sent_map).dropna()
                if not scores.empty:
                    return float(scores.mean())
        except Exception:
            pass
        return 0.0

    @staticmethod
    def _get_weather_factor(dbm) -> float:
        """
        Weather risk factor.
        High temperature or heavy rainfall → positive factor (price up).
        """
        try:
            w_df = dbm.get_weather_logs()
            if not w_df.empty:
                latest = w_df.iloc[-1]
                temp = float(latest.get("temperature", 25))
                rain = float(latest.get("rainfall", 0))
                factor = 0.0
                if temp > 40:
                    factor += 0.5
                if rain > 50:
                    factor += 0.5
                return factor
        except Exception:
            pass
        return 0.0


# ---------------------------------------------------------------------------
# Module-level singleton & convenience functions
# ---------------------------------------------------------------------------

_generator = IntradayStreamGenerator()


def start_realtime_generator(commodity: str, mandi: str) -> None:
    """Start the global intraday stream generator."""
    _generator.start(commodity, mandi)


def stop_realtime_generator() -> None:
    """Stop the global intraday stream generator."""
    _generator.stop()


def get_stream_status() -> Dict:
    """Return current stream status metrics."""
    return _generator.get_status()


def get_intraday_trades(commodity: str, mandi: str, limit: int = 50):
    """
    Convenience wrapper — fetches latest intraday trades from DB.
    Falls back to an empty DataFrame if table is missing.
    """
    try:
        import database.db_manager as dbm
        return dbm.get_latest_intraday_trades(commodity, mandi, limit)
    except Exception:
        import pandas as pd
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# CLI entry point (for manual testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import database.db_manager as dbm
    dbm.init_db()

    print("Starting real-time stream generator (Ctrl+C to stop)...")
    start_realtime_generator("Onion", "Azadpur")

    try:
        while True:
            time.sleep(5)
            status = get_stream_status()
            print(f"  ticks={status['ticks_generated']}  "
                  f"uptime={status['uptime_seconds']}s  "
                  f"rate={status['ticks_per_minute']}/min")
    except KeyboardInterrupt:
        stop_realtime_generator()
        print("\nStopped.")
