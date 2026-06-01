"""
RACE Forecasting Engine — Regime-Adaptive Competitive Ensemble
================================================================
IP-grade multi-model ensemble that dynamically adjusts model weights
based on the detected market regime (STABLE / VOLATILE / CRISIS).

Models: XGBoost, LightGBM, CatBoost
Weighting: Inverse-MAPE competitive scoring with regime penalty/bonus.
Regime: Detected via Hidden Markov Model (RegimeDetector).

Public API
----------
    forecaster = RACEForecaster()
    result = forecaster.forecast(data, commodity, mandi, horizon=30)
    result = forecaster.forecast_realtime(data, commodity, mandi, intraday_df)
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import timedelta
import warnings

warnings.filterwarnings("ignore")

from .regime_detector import RegimeDetector, RegimeState
from .feature_factory import FeatureFactory


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class ForecastResult:
    """Container for RACE forecast output."""
    forecast_df: pd.DataFrame          # date, forecast_price, lower_bound, upper_bound
    regime: RegimeState                 # current market regime
    model_weights: Dict[str, float]    # e.g. {"XGBoost": 0.45, "LightGBM": 0.30, ...}
    confidence: float                  # 0.0–1.0
    metadata: Dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Model wrappers (thin adapters around each library)
# ---------------------------------------------------------------------------

class _BaseModel:
    """Abstract model wrapper."""
    name: str = "base"

    def fit(self, X, y):
        raise NotImplementedError

    def predict(self, X) -> np.ndarray:
        raise NotImplementedError


class _XGBModel(_BaseModel):
    name = "XGBoost"

    def __init__(self):
        import xgboost as xgb
        self.model = xgb.XGBRegressor(
            objective="reg:squarederror",
            n_estimators=120,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.8,
            colsample_bytree=0.8,
            verbosity=0,
            random_state=42,
        )

    def fit(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict(X)


class _LGBModel(_BaseModel):
    name = "LightGBM"

    def __init__(self):
        try:
            import lightgbm as lgb
            self.model = lgb.LGBMRegressor(
                n_estimators=120,
                max_depth=5,
                learning_rate=0.08,
                subsample=0.8,
                colsample_bytree=0.8,
                verbose=-1,
                random_state=42,
            )
        except ImportError:
            self.model = None

    def fit(self, X, y):
        if self.model is not None:
            self.model.fit(X, y)

    def predict(self, X):
        if self.model is not None:
            return self.model.predict(X)
        return np.zeros(len(X))


class _CatModel(_BaseModel):
    name = "CatBoost"

    def __init__(self):
        try:
            from catboost import CatBoostRegressor
            self.model = CatBoostRegressor(
                iterations=120,
                depth=5,
                learning_rate=0.08,
                verbose=0,
                random_seed=42,
            )
        except ImportError:
            self.model = None

    def fit(self, X, y):
        if self.model is not None:
            self.model.fit(X, y)

    def predict(self, X):
        if self.model is not None:
            return self.model.predict(X)
        return np.zeros(len(X))


# ---------------------------------------------------------------------------
# RACE Forecaster
# ---------------------------------------------------------------------------

class RACEForecaster:
    """
    Regime-Adaptive Competitive Ensemble forecaster.

    1. Detects the market regime via HMM.
    2. Trains XGBoost, LightGBM, CatBoost on expanding-window CV.
    3. Assigns weights via inverse-MAPE scoring, adjusted by regime.
    4. Generates a weighted ensemble 30-day recursive forecast.
    """

    def __init__(self):
        self.regime_detector = RegimeDetector()
        self.feature_factory: Optional[FeatureFactory] = None
        self.models: List[_BaseModel] = []
        self._fitted = False
        self._cached_weights: Dict[str, float] = {}
        self._cached_feature_cols: List[str] = []

    # ----- Public API -----

    def forecast(
        self,
        data: pd.DataFrame,
        commodity: str,
        mandi: str,
        horizon: int = 30,
        weather_df: Optional[pd.DataFrame] = None,
    ) -> ForecastResult:
        """
        Full RACE forecast pipeline.

        Parameters
        ----------
        data : DataFrame with at least ['date', 'price'] columns.
        commodity, mandi : identifiers.
        horizon : forecast horizon in days.
        weather_df : optional weather DataFrame.

        Returns
        -------
        ForecastResult
        """
        data = data.copy()
        data["date"] = pd.to_datetime(data["date"])
        data = data.sort_values("date").reset_index(drop=True)

        if len(data) < 30:
            return self._fallback_forecast(data, commodity, mandi, horizon)

        # 1. Regime Detection
        regime_state = self.regime_detector.detect_regime(data["price"])

        # 2. Feature Engineering
        self.feature_factory = FeatureFactory(commodity=commodity)
        featured = self.feature_factory.build_features(
            data, target_col="price", weather_df=weather_df,
        )
        feature_cols = self.feature_factory.get_feature_columns(featured)
        self._cached_feature_cols = feature_cols

        # 3. Prepare training data
        X = featured[feature_cols].values
        y = featured["price"].values

        # 4. Train models & competitive scoring
        self.models = [_XGBModel(), _LGBModel(), _CatModel()]
        # Filter out models that couldn't import
        self.models = [m for m in self.models if m.model is not None]

        model_scores = self._competitive_cv(X, y, n_splits=3)
        weights = self._compute_weights(model_scores, regime_state.regime)
        self._cached_weights = weights

        # 5. Train on full data
        for m in self.models:
            m.fit(X, y)
        self._fitted = True

        # 6. Recursive forecast
        forecast_df = self._recursive_forecast(
            data, featured, feature_cols, weights, horizon
        )

        # 7. Confidence interval
        rmse_val = self._estimate_rmse(X, y)
        forecast_df = self._add_confidence_bands(forecast_df, rmse_val, horizon)
        forecast_df["commodity"] = commodity
        forecast_df["mandi"] = mandi

        return ForecastResult(
            forecast_df=forecast_df,
            regime=regime_state,
            model_weights=weights,
            confidence=round(regime_state.confidence, 4),
            metadata={
                "horizon": horizon,
                "training_samples": len(data),
                "feature_count": len(feature_cols),
                "rmse": round(rmse_val, 2),
            },
        )

    def forecast_realtime(
        self,
        data: pd.DataFrame,
        commodity: str,
        mandi: str,
        intraday_df: Optional[pd.DataFrame] = None,
    ) -> ForecastResult:
        """
        Fast-path forecast that incorporates intraday ticks.

        Uses cached models if available; otherwise falls back to
        full ``forecast()`` call.
        """
        if intraday_df is not None and not intraday_df.empty:
            # Append today's intraday TRADE ticks as synthetic daily rows
            trades = intraday_df[intraday_df["trade_type"] == "TRADE"].copy()
            if not trades.empty:
                trades["timestamp"] = pd.to_datetime(trades["timestamp"])
                latest_trade = trades.sort_values("timestamp").iloc[-1]
                today_row = pd.DataFrame([{
                    "date": pd.Timestamp.now().normalize(),
                    "price": float(latest_trade["price"]),
                    "arrival": float(trades["quantity"].sum()),
                    "commodity": commodity,
                    "mandi": mandi,
                }])
                # Append only if today isn't already in data
                data = data.copy()
                data["date"] = pd.to_datetime(data["date"])
                if pd.Timestamp.now().normalize() not in data["date"].values:
                    data = pd.concat([data, today_row], ignore_index=True)

        return self.forecast(data, commodity, mandi, horizon=30)

    # ----- Competitive Cross-Validation -----

    def _competitive_cv(self, X: np.ndarray, y: np.ndarray,
                        n_splits: int = 3) -> Dict[str, float]:
        """
        Expanding-window time-series CV.
        Returns {model_name: average_mape} dict.
        """
        n = len(X)
        if n < 40:
            # Not enough for CV — return equal scores
            return {m.name: 5.0 for m in self.models}

        fold_size = max(5, n // (n_splits + 1))
        scores: Dict[str, list] = {m.name: [] for m in self.models}

        for fold in range(n_splits):
            train_end = n - (n_splits - fold) * fold_size
            val_start = train_end
            val_end = min(val_start + fold_size, n)

            if train_end < 30 or val_start >= n:
                continue

            X_train, y_train = X[:train_end], y[:train_end]
            X_val, y_val = X[val_start:val_end], y[val_start:val_end]

            for m in self.models:
                try:
                    m.fit(X_train, y_train)
                    preds = m.predict(X_val)
                    mape = np.mean(np.abs((y_val - preds) / (y_val + 1e-9))) * 100
                    scores[m.name].append(mape)
                except Exception:
                    scores[m.name].append(10.0)  # penalty

        return {name: np.mean(vals) if vals else 10.0
                for name, vals in scores.items()}

    def _compute_weights(self, model_scores: Dict[str, float],
                         regime: str) -> Dict[str, float]:
        """
        Inverse-MAPE weighting with regime adjustments.
        """
        # Inverse MAPE
        inv_scores = {k: 1.0 / (v + 1e-6) for k, v in model_scores.items()}

        # Regime bonuses: in VOLATILE/CRISIS, boost CatBoost (better at tail risks)
        if regime == "CRISIS":
            inv_scores["CatBoost"] = inv_scores.get("CatBoost", 0) * 1.4
            inv_scores["XGBoost"] = inv_scores.get("XGBoost", 0) * 0.9
        elif regime == "VOLATILE":
            inv_scores["CatBoost"] = inv_scores.get("CatBoost", 0) * 1.2
            inv_scores["LightGBM"] = inv_scores.get("LightGBM", 0) * 1.1

        total = sum(inv_scores.values())
        return {k: round(v / total, 4) for k, v in inv_scores.items()} if total > 0 \
            else {k: round(1.0 / len(inv_scores), 4) for k in inv_scores}

    # ----- Recursive Forecast -----

    def _recursive_forecast(
        self,
        original_data: pd.DataFrame,
        featured: pd.DataFrame,
        feature_cols: List[str],
        weights: Dict[str, float],
        horizon: int,
    ) -> pd.DataFrame:
        """Generate *horizon*-day forecast using recursive prediction."""
        current_data = original_data.copy()
        last_date = current_data["date"].max()
        future_dates = []
        forecast_prices = []

        for i in range(1, horizon + 1):
            next_date = last_date + timedelta(days=i)

            # Build a temporary row and re-engineer features
            next_row = pd.DataFrame([{
                "date": next_date,
                "price": current_data["price"].iloc[-1],  # placeholder
                "arrival": current_data["arrival"].iloc[-1] if "arrival" in current_data.columns else 200,
                "commodity": current_data.get("commodity", pd.Series(["Unknown"])).iloc[-1],
                "mandi": current_data.get("mandi", pd.Series(["Unknown"])).iloc[-1],
            }])

            temp_df = pd.concat([current_data, next_row], ignore_index=True)
            temp_features = self.feature_factory.build_features(temp_df, target_col="price")

            X_pred = temp_features[feature_cols].iloc[[-1]].values

            # Weighted ensemble prediction
            pred_price = 0.0
            for m in self.models:
                w = weights.get(m.name, 0)
                try:
                    p = m.predict(X_pred)[0]
                    pred_price += w * p
                except Exception:
                    pass

            future_dates.append(next_date)
            forecast_prices.append(round(pred_price, 2))

            # Update loop data for recursion
            next_row["price"] = pred_price
            current_data = pd.concat([current_data, next_row], ignore_index=True)

        return pd.DataFrame({
            "date": future_dates,
            "forecast_price": forecast_prices,
        })

    # ----- Helpers -----

    def _estimate_rmse(self, X: np.ndarray, y: np.ndarray) -> float:
        """Quick RMSE on last 5 samples (validation proxy)."""
        if len(X) < 10:
            return float(np.std(y))
        val_size = min(5, len(X) // 5)
        X_val, y_val = X[-val_size:], y[-val_size:]
        preds = np.zeros(val_size)
        for m in self.models:
            w = self._cached_weights.get(m.name, 1.0 / len(self.models))
            try:
                preds += w * m.predict(X_val)
            except Exception:
                pass
        return float(np.sqrt(np.mean((y_val - preds) ** 2)))

    @staticmethod
    def _add_confidence_bands(df: pd.DataFrame, rmse: float,
                              horizon: int) -> pd.DataFrame:
        """Add expanding confidence intervals."""
        time_steps = np.arange(1, len(df) + 1)
        # Uncertainty grows logarithmically
        margin = 1.96 * rmse * (np.log(time_steps + 1) + 0.5)
        df["lower_bound"] = df["forecast_price"] - margin
        df["upper_bound"] = df["forecast_price"] + margin
        return df

    def _fallback_forecast(self, data: pd.DataFrame, commodity: str,
                           mandi: str, horizon: int) -> ForecastResult:
        """Simple random-walk fallback for insufficient data."""
        last_date = pd.to_datetime(data["date"].max())
        last_price = float(data["price"].iloc[-1])
        np.random.seed(42)

        dates = [last_date + timedelta(days=i) for i in range(1, horizon + 1)]
        changes = np.random.normal(0, last_price * 0.02, horizon)
        prices = last_price + np.cumsum(changes)
        ci = np.linspace(last_price * 0.05, last_price * 0.15, horizon)

        df = pd.DataFrame({
            "date": dates,
            "forecast_price": prices,
            "lower_bound": prices - ci,
            "upper_bound": prices + ci,
            "commodity": commodity,
            "mandi": mandi,
        })

        return ForecastResult(
            forecast_df=df,
            regime=RegimeState(regime="STABLE", confidence=0.3,
                               features={"reason": "fallback"}),
            model_weights={"XGBoost": 1.0},
            confidence=0.3,
            metadata={"fallback": True},
        )
