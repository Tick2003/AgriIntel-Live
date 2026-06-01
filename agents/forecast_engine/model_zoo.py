"""
RACE Model Zoo — Competing Forecast Models
============================================
Registry of all models that compete inside the RACE ensemble.
Each model implements the BaseForecaster interface to ensure
uniform training, prediction, and explainability.

Models:
- XGBoostForecaster
- LightGBMForecaster
- CatBoostForecaster
- LinearTrendForecaster (baseline)
"""

import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, Optional
import warnings
import hashlib
from datetime import datetime

warnings.filterwarnings("ignore")


class BaseForecaster(ABC):
    """Abstract base class for all RACE ensemble members."""

    @abstractmethod
    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train the model on feature matrix X and target y."""
        ...

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generate point predictions."""
        ...

    @abstractmethod
    def get_feature_importance(self) -> Dict[str, float]:
        """Return dict of {feature_name: importance_score}."""
        ...

    @abstractmethod
    def get_model_id(self) -> str:
        """Return unique model identifier string."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...


class XGBoostForecaster(BaseForecaster):
    """XGBoost gradient-boosted tree regressor."""

    def __init__(self):
        import xgboost as xgb
        self._model = xgb.XGBRegressor(
            objective="reg:squarederror",
            n_estimators=150,
            learning_rate=0.08,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            verbosity=0,
            random_state=42,
        )
        self._feature_names = []
        self._version = f"XGB-{datetime.now().strftime('%Y%m%d')}"

    @property
    def name(self) -> str:
        return "XGBoost"

    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        self._feature_names = list(X.columns)
        self._model.fit(X, y)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self._model.predict(X)

    def get_feature_importance(self) -> Dict[str, float]:
        importances = self._model.feature_importances_
        return dict(zip(self._feature_names, importances.tolist()))

    def get_model_id(self) -> str:
        return self._version


class LightGBMForecaster(BaseForecaster):
    """LightGBM leaf-wise gradient-boosted tree regressor."""

    def __init__(self):
        self._model = None
        self._feature_names = []
        self._version = f"LGBM-{datetime.now().strftime('%Y%m%d')}"

    @property
    def name(self) -> str:
        return "LightGBM"

    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        try:
            import lightgbm as lgb
            self._feature_names = list(X.columns)
            self._model = lgb.LGBMRegressor(
                n_estimators=150,
                learning_rate=0.08,
                num_leaves=31,
                max_depth=-1,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=1.0,
                verbose=-1,
                random_state=42,
            )
            self._model.fit(X, y)
        except ImportError:
            # Fallback to XGBoost if lightgbm not installed
            import xgboost as xgb
            self._feature_names = list(X.columns)
            self._model = xgb.XGBRegressor(
                n_estimators=120, learning_rate=0.1, max_depth=5,
                verbosity=0, random_state=43,
            )
            self._model.fit(X, y)
            self._version = f"LGBM-FALLBACK-{datetime.now().strftime('%Y%m%d')}"

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self._model.predict(X)

    def get_feature_importance(self) -> Dict[str, float]:
        importances = self._model.feature_importances_
        return dict(zip(self._feature_names, importances.tolist()))

    def get_model_id(self) -> str:
        return self._version


class CatBoostForecaster(BaseForecaster):
    """CatBoost gradient-boosted tree — superior with categorical features."""

    def __init__(self):
        self._model = None
        self._feature_names = []
        self._version = f"CB-{datetime.now().strftime('%Y%m%d')}"

    @property
    def name(self) -> str:
        return "CatBoost"

    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        try:
            from catboost import CatBoostRegressor
            self._feature_names = list(X.columns)
            self._model = CatBoostRegressor(
                iterations=150,
                learning_rate=0.08,
                depth=6,
                l2_leaf_reg=3.0,
                verbose=0,
                random_seed=42,
            )
            self._model.fit(X, y)
        except ImportError:
            # Fallback
            import xgboost as xgb
            self._feature_names = list(X.columns)
            self._model = xgb.XGBRegressor(
                n_estimators=120, learning_rate=0.1, max_depth=5,
                verbosity=0, random_state=44,
            )
            self._model.fit(X, y)
            self._version = f"CB-FALLBACK-{datetime.now().strftime('%Y%m%d')}"

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self._model.predict(X)

    def get_feature_importance(self) -> Dict[str, float]:
        importances = self._model.feature_importances_
        return dict(zip(self._feature_names, importances.tolist()))

    def get_model_id(self) -> str:
        return self._version


class LinearTrendForecaster(BaseForecaster):
    """Simple linear regression baseline — effective in stable regimes."""

    def __init__(self):
        from sklearn.linear_model import Ridge
        self._model = Ridge(alpha=1.0)
        self._feature_names = []
        self._version = f"LIN-{datetime.now().strftime('%Y%m%d')}"

    @property
    def name(self) -> str:
        return "LinearTrend"

    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        self._feature_names = list(X.columns)
        self._model.fit(X, y)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self._model.predict(X)

    def get_feature_importance(self) -> Dict[str, float]:
        coeffs = np.abs(self._model.coef_)
        total = coeffs.sum() + 1e-9
        normalised = coeffs / total
        return dict(zip(self._feature_names, normalised.tolist()))

    def get_model_id(self) -> str:
        return self._version


# Registry for dynamic model instantiation
MODEL_REGISTRY = {
    "XGBoost": XGBoostForecaster,
    "LightGBM": LightGBMForecaster,
    "CatBoost": CatBoostForecaster,
    "LinearTrend": LinearTrendForecaster,
}


def create_model(name: str) -> BaseForecaster:
    """Factory function to create a model by name."""
    cls = MODEL_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown model: {name}. Available: {list(MODEL_REGISTRY.keys())}")
    return cls()
