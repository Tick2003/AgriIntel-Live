"""
AGENT 3 — SHOCK MONITORING AGENT (v2.0-REALTIME)
==================================================
Detects anomalies and market shocks.
Supports both daily and intraday tick-level shock detection.
"""

import pandas as pd
import numpy as np


class AnomalyDetectionEngine:
    """
    AGENT 3 — SHOCK MONITORING AGENT
    Role: Detects anomalies and market shocks.
    Goal: Detect abnormal price movements by comparing actual prices with model predictions.
    """
    def __init__(self):
        pass

    def detect_shocks(self, actual_data: pd.DataFrame, forecast_data: pd.DataFrame) -> dict:
        """
        Compare actuals vs forecasts boundaries or just check for high volatility if forecast not historically aligned.
        For this MVP, we check if the latest actual price is within the confidence interval of the forecast 
        (assuming forecast was made for today - strictly speaking we'd need past forecasts, 
        but we'll simulate 'deviation from trend' here).
        
        Alternatively, we can just look solely at the latest price drop/rise > threshold.
        """
        if actual_data.empty:
            return {"alert": False, "message": "No data"}
            
        latest_price = actual_data['price'].iloc[-1]
        prev_price = actual_data['price'].iloc[-2] if len(actual_data) > 1 else latest_price
        
        pct_change = (latest_price - prev_price) / prev_price if prev_price != 0 else 0
        
        shock_detected = False
        severity = "None"
        score = 0
        
        # Simple threshold logic
        if abs(pct_change) > 0.15: # 15% change
            shock_detected = True
            severity = "High"
            score = 100
        elif abs(pct_change) > 0.05: # 5% change
            shock_detected = True
            severity = "Medium"
            score = 50
            
        return {
            "is_shock": shock_detected,
            "severity": severity,
            "score": score,
            "details": f"Price changed by {pct_change:.1%} recently."
        }

    def detect_intraday_shocks(self, intraday_df: pd.DataFrame,
                                daily_modal_price: float) -> dict:
        """
        Real-time intraday shock detection.

        Triggers if any intraday TRADE tick deviates beyond the
        99% confidence interval (±3σ) from the daily modal price.

        Parameters
        ----------
        intraday_df : DataFrame
            Recent intraday trades (from ``intraday_trades`` table).
        daily_modal_price : float
            The anchor daily modal price.

        Returns
        -------
        dict with keys: is_shock, severity, shocks (list of dicts),
        max_deviation_pct, tick_count.
        """
        if intraday_df.empty or daily_modal_price <= 0:
            return {
                "is_shock": False,
                "severity": "None",
                "shocks": [],
                "max_deviation_pct": 0.0,
                "tick_count": 0,
            }

        # Filter to TRADE ticks only
        trades = intraday_df[intraday_df["trade_type"] == "TRADE"].copy()
        if trades.empty:
            return {
                "is_shock": False,
                "severity": "None",
                "shocks": [],
                "max_deviation_pct": 0.0,
                "tick_count": 0,
            }

        # Calculate deviations
        trades["deviation_pct"] = (
            (trades["price"] - daily_modal_price) / daily_modal_price * 100
        )
        trades["abs_deviation_pct"] = trades["deviation_pct"].abs()

        # Compute dynamic σ from the tick series
        if len(trades) >= 5:
            sigma = trades["price"].std()
        else:
            sigma = daily_modal_price * 0.02  # 2% default

        threshold_3sigma = 3 * sigma
        threshold_pct = (threshold_3sigma / daily_modal_price) * 100

        # Detect shocks (beyond 3σ OR >5% deviation)
        effective_threshold = max(threshold_pct, 5.0)
        shock_mask = trades["abs_deviation_pct"] > effective_threshold
        shock_ticks = trades[shock_mask]

        max_dev = float(trades["abs_deviation_pct"].max())

        shocks_list = []
        for _, row in shock_ticks.iterrows():
            shocks_list.append({
                "timestamp": row.get("timestamp", ""),
                "price": float(row["price"]),
                "deviation_pct": round(float(row["deviation_pct"]), 2),
                "quantity": float(row.get("quantity", 0)),
            })

        # Severity classification
        if len(shocks_list) > 0:
            is_shock = True
            if max_dev > 10:
                severity = "Critical"
            elif max_dev > 7:
                severity = "High"
            else:
                severity = "Medium"
        else:
            is_shock = False
            severity = "None"

        return {
            "is_shock": is_shock,
            "severity": severity,
            "shocks": shocks_list[-5:],  # last 5 shock events
            "max_deviation_pct": round(max_dev, 2),
            "tick_count": len(trades),
        }
