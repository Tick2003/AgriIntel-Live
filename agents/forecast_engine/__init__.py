"""
AgriIntel RACE Forecasting Engine
=================================
Regime-Adaptive Competitive Ensemble (RACE) — IP Core.

This package implements a multi-model ensemble forecasting system
that dynamically adjusts model weights based on detected market regime
(Stable / Volatile / Crisis) using Hidden Markov Models and
competitive time-series cross-validation.
"""

from .ensemble import RACEForecaster, ForecastResult

__all__ = ["RACEForecaster", "ForecastResult"]
