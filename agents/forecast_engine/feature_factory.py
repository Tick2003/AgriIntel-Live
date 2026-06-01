"""
RACE Feature Factory — Centralised Feature Engineering
=======================================================
Production-grade feature pipeline used by all models in the
RACE ensemble. Ensures consistent, reproducible feature vectors.

Features:
- Technical indicators: RSI, MACD, Bollinger Bands, ATR
- Temporal: day_of_week, month, quarter, is_harvest_season
- Lag features: 1d, 3d, 7d, 14d, 30d + rolling stats
- Seasonal decomposition components (STL)
- Domain-specific: festival_proximity, days_since_last_shock
"""

import numpy as np
import pandas as pd
from typing import List, Optional
import warnings

warnings.filterwarnings("ignore")


# Indian agricultural harvest calendar (approximate months)
HARVEST_CALENDAR = {
    "Onion": [11, 12, 1, 2, 3],        # Rabi harvest
    "Potato": [1, 2, 3],                # Rabi harvest
    "Tomato": [10, 11, 12, 1, 2, 3],    # Year-round, peak winter
    "Wheat": [3, 4, 5],                 # Rabi harvest
    "Rice": [9, 10, 11],                # Kharif harvest
    "Maize": [9, 10],                   # Kharif harvest
    "Soyabean": [10, 11],               # Kharif harvest
    "Mustard": [2, 3, 4],               # Rabi harvest
    "Cotton": [10, 11, 12],             # Kharif harvest
    "Sugarcane": [11, 12, 1, 2, 3, 4],  # Crushing season
}

# Indian festivals that affect agri markets (approximate month-day ranges)
FESTIVAL_MONTHS = [1, 3, 8, 10, 11]  # Makar Sankranti, Holi, Independence, Navratri, Diwali


class FeatureFactory:
    """
    Centralised feature engineering pipeline for the RACE ensemble.

    All models consume the same feature matrix to ensure fair
    competitive scoring.
    """

    def __init__(self, commodity: str = "General"):
        self.commodity = commodity

    def build_features(
        self,
        df: pd.DataFrame,
        target_col: str = "price",
        weather_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Build the full feature matrix from a price DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            Must contain columns: ['date', target_col].
            Optionally: 'arrival', 'price_min', 'price_max'.
        target_col : str
            The price column to derive features from.
        weather_df : pd.DataFrame, optional
            Weather data with ['date', 'temperature', 'rainfall'].

        Returns
        -------
        pd.DataFrame
            Original columns + all engineered features.
        """
        out = df.copy()
        out["date"] = pd.to_datetime(out["date"])
        out = out.sort_values("date").reset_index(drop=True)

        # --- Temporal ---
        out["day_of_week"] = out["date"].dt.dayofweek
        out["month"] = out["date"].dt.month
        out["quarter"] = out["date"].dt.quarter
        out["day_of_year"] = out["date"].dt.dayofyear

        # Harvest season flag
        harvest_months = HARVEST_CALENDAR.get(self.commodity, [])
        out["is_harvest"] = out["month"].isin(harvest_months).astype(int)

        # Festival proximity
        out["festival_proximity"] = out["month"].isin(FESTIVAL_MONTHS).astype(int)

        # --- Lag features ---
        for lag in [1, 3, 7, 14, 30]:
            out[f"lag_{lag}"] = out[target_col].shift(lag)

        # --- Rolling statistics ---
        for window in [7, 14, 30]:
            out[f"roll_mean_{window}"] = out[target_col].rolling(window).mean()
            out[f"roll_std_{window}"] = out[target_col].rolling(window).std()
            out[f"roll_skew_{window}"] = out[target_col].rolling(window).skew()

        # --- Technical indicators ---
        self._add_rsi(out, target_col)
        self._add_macd(out, target_col)
        self._add_bollinger(out, target_col)
        self._add_atr(out, target_col)

        # --- Price velocity ---
        out["price_velocity_7"] = out[target_col].pct_change(7)
        out["price_velocity_14"] = out[target_col].pct_change(14)

        # --- Arrival features (if present) ---
        if "arrival" in out.columns:
            out["arrival_lag_1"] = out["arrival"].shift(1)
            out["arrival_roll_7"] = out["arrival"].rolling(7).mean()
            out["arrival_zscore"] = (
                (out["arrival"] - out["arrival"].rolling(30).mean())
                / (out["arrival"].rolling(30).std() + 1e-9)
            )

        # --- Price spread (if min/max present) ---
        if "price_min" in out.columns and "price_max" in out.columns:
            out["price_spread"] = out["price_max"] - out["price_min"]
            out["spread_pct"] = out["price_spread"] / (out[target_col] + 1e-9)

        # --- Weather features (if provided) ---
        if weather_df is not None and not weather_df.empty:
            weather_df = weather_df.copy()
            weather_df["date"] = pd.to_datetime(weather_df["date"])
            out = pd.merge(out, weather_df[["date", "temperature", "rainfall"]],
                           on="date", how="left")
            out["temperature"] = out["temperature"].ffill().fillna(25.0)
            out["rainfall"] = out["rainfall"].fillna(0.0)
            out["rain_lag_1"] = out["rainfall"].shift(1).fillna(0)
            out["temp_lag_1"] = out["temperature"].shift(1).fillna(25)

        # --- STL seasonal decomposition ---
        self._add_stl(out, target_col)

        # --- Days since last shock ---
        self._add_shock_distance(out, target_col)

        # Fill NaN from lag/rolling operations
        out = out.bfill().fillna(0)

        return out

    def get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """Return list of feature column names (excludes date, target, identifiers)."""
        exclude = {
            "date", "price", "price_modal", "price_min", "price_max",
            "arrival", "commodity", "mandi", "unit", "id",
            "date_ordinal", "trend", "resid",
            "temperature", "rainfall",  # raw weather kept separately
        }
        return [c for c in df.columns if c not in exclude and df[c].dtype in [np.float64, np.int64, np.float32, np.int32, float, int]]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _add_rsi(df: pd.DataFrame, col: str, period: int = 14):
        delta = df[col].diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / (loss + 1e-9)
        df["rsi"] = 100 - (100 / (1 + rs))

    @staticmethod
    def _add_macd(df: pd.DataFrame, col: str):
        exp12 = df[col].ewm(span=12, adjust=False).mean()
        exp26 = df[col].ewm(span=26, adjust=False).mean()
        df["macd"] = exp12 - exp26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

    @staticmethod
    def _add_bollinger(df: pd.DataFrame, col: str, period: int = 20):
        mid = df[col].rolling(period).mean()
        std = df[col].rolling(period).std()
        df["bb_upper"] = mid + 2 * std
        df["bb_lower"] = mid - 2 * std
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / (mid + 1e-9)
        df["bb_position"] = (df[col] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"] + 1e-9)

    @staticmethod
    def _add_atr(df: pd.DataFrame, col: str, period: int = 14):
        """Average True Range (proxy — using single-price series)."""
        high_low = df[col].rolling(2).max() - df[col].rolling(2).min()
        df["atr"] = high_low.rolling(period).mean()

    @staticmethod
    def _add_stl(df: pd.DataFrame, col: str):
        """Seasonal-Trend decomposition using LOESS (STL)."""
        try:
            from statsmodels.tsa.seasonal import STL
            if len(df) >= 60:
                stl = STL(df[col].values, period=30, robust=True)
                result = stl.fit()
                df["stl_trend"] = result.trend
                df["stl_seasonal"] = result.seasonal
                df["stl_residual"] = result.resid
                return
        except Exception:
            pass
        # Fallback
        df["stl_trend"] = df[col].rolling(30, min_periods=1).mean()
        df["stl_seasonal"] = df[col] - df["stl_trend"]
        df["stl_residual"] = 0.0

    @staticmethod
    def _add_shock_distance(df: pd.DataFrame, col: str, threshold: float = 0.05):
        """Days since last price shock (|daily return| > threshold)."""
        returns = df[col].pct_change().abs()
        shock_mask = returns > threshold
        days_since = []
        counter = 999  # large default
        for is_shock in shock_mask:
            if is_shock:
                counter = 0
            else:
                counter += 1
            days_since.append(counter)
        df["days_since_shock"] = days_since
