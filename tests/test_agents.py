"""
Unit Tests for Agents (Forecast, Risk, Shock, Decision)
========================================================
Tests ML agents with synthetic data to ensure no runtime errors.
"""

import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestForecastAgent:
    """Tests for ForecastingAgent."""

    def test_generate_forecast_legacy(self, sample_price_df_with_price_col):
        """Test legacy XGBoost forecast generation."""
        from agents.forecast_execution import ForecastingAgent

        agent = ForecastingAgent()
        result = agent._generate_legacy_forecast(
            sample_price_df_with_price_col, "Onion", "Azadpur"
        )

        assert not result.empty
        assert len(result) == 30
        assert "forecast_price" in result.columns
        assert "lower_bound" in result.columns
        assert "upper_bound" in result.columns

    def test_generate_forecast_fallback(self):
        """Test fallback forecast with minimal data."""
        from agents.forecast_execution import ForecastingAgent

        agent = ForecastingAgent()
        # Only 10 days — too few for full model, should use fallback
        df = pd.DataFrame({
            "date": pd.date_range(end=datetime.today(), periods=10),
            "price": np.random.uniform(2000, 3000, 10),
            "arrival": np.random.randint(50, 200, 10),
        })

        result = agent.generate_forecasts(df, "Potato", "Agra")
        assert not result.empty
        assert len(result) == 30

    def test_generate_forecast_empty_data(self):
        """Test forecast with empty data returns empty."""
        from agents.forecast_execution import ForecastingAgent

        agent = ForecastingAgent()
        result = agent._generate_fallback(pd.DataFrame({"date": [], "price": []}), "X", "Y")
        # With truly empty data, may fail gracefully
        assert isinstance(result, pd.DataFrame)


class TestRiskEngine:
    """Tests for MarketRiskEngine."""

    def test_calculate_risk_score_low(self):
        """Test risk score with low volatility."""
        from agents.risk_scoring import MarketRiskEngine

        engine = MarketRiskEngine()
        result = engine.calculate_risk_score(
            shock_info={"is_shock": False},
            forecast_std=50,
            market_volatility=0.005,
        )

        assert "risk_score" in result
        assert 0 <= result["risk_score"] <= 100
        assert "risk_level" in result
        assert "breakdown" in result
        assert "explanation_tags" in result

    def test_calculate_risk_score_high(self):
        """Test risk score with high volatility and shock."""
        from agents.risk_scoring import MarketRiskEngine

        engine = MarketRiskEngine()
        result = engine.calculate_risk_score(
            shock_info={"is_shock": True, "severity": "High"},
            forecast_std=1000,
            market_volatility=0.05,
            sentiment_score=-1.0,
            arrival_anomaly=0.8,
            weather_risk=1.0,
        )

        assert result["risk_score"] >= 50
        assert result["risk_level"] in ("High", "Critical")

    def test_determine_regime(self):
        """Test market regime classification."""
        from agents.risk_scoring import MarketRiskEngine

        engine = MarketRiskEngine()

        stable = engine.determine_regime(0.005, False)
        assert stable == "Stable"

        volatile = engine.determine_regime(0.03, False)
        assert volatile == "Volatile"

        crisis = engine.determine_regime(0.05, True)
        assert crisis == "Crisis"

    def test_calculate_realtime_risk_no_shock(self):
        """Test realtime risk with no intraday shock."""
        from agents.risk_scoring import MarketRiskEngine

        engine = MarketRiskEngine()
        base = {
            "risk_score": 40, "risk_level": "Moderate", "regime": "Stable",
            "breakdown": {"Volatility": 20, "Market Shocks": 10, "News Sentiment": 5, "Supply/Weather": 5},
            "explanation_tags": [],
        }
        result = engine.calculate_realtime_risk(base, {"is_shock": False})
        assert result["risk_score"] == 40

    def test_calculate_realtime_risk_with_shock(self):
        """Test realtime risk augmentation with shock."""
        from agents.risk_scoring import MarketRiskEngine

        engine = MarketRiskEngine()
        base = {
            "risk_score": 40, "risk_level": "Moderate", "regime": "Stable",
            "breakdown": {"Volatility": 20, "Market Shocks": 10, "News Sentiment": 5, "Supply/Weather": 5},
            "explanation_tags": [],
        }
        shock = {"is_shock": True, "severity": "Critical", "shocks": [{"price": 120}]}
        result = engine.calculate_realtime_risk(base, shock)
        assert result["risk_score"] == 60
        assert "Intraday Shocks" in result["breakdown"]


class TestShockMonitoring:
    """Tests for AnomalyDetectionEngine."""

    def test_detect_shocks_no_anomaly(self, sample_price_df_with_price_col, sample_forecast_df):
        """Test shock detection with normal data."""
        from agents.shock_monitoring import AnomalyDetectionEngine

        engine = AnomalyDetectionEngine()
        result = engine.detect_shocks(sample_price_df_with_price_col, sample_forecast_df)

        assert "is_shock" in result
        assert isinstance(result["is_shock"], bool)

    def test_detect_intraday_shocks_normal(self, sample_intraday_df):
        """Test intraday shock detection with normal ticks."""
        from agents.shock_monitoring import AnomalyDetectionEngine

        engine = AnomalyDetectionEngine()
        result = engine.detect_intraday_shocks(sample_intraday_df, daily_modal_price=2500.0)

        assert "is_shock" in result
        assert "severity" in result
        assert "shocks" in result
        assert "tick_count" in result

    def test_detect_intraday_shocks_empty(self):
        """Test intraday shock detection with empty data."""
        from agents.shock_monitoring import AnomalyDetectionEngine

        engine = AnomalyDetectionEngine()
        result = engine.detect_intraday_shocks(pd.DataFrame(), daily_modal_price=2500.0)

        assert result["is_shock"] is False

    def test_detect_intraday_shocks_spike(self):
        """Test intraday shock detection with price spike."""
        from agents.shock_monitoring import AnomalyDetectionEngine

        engine = AnomalyDetectionEngine()
        ticks = pd.DataFrame([
            {"timestamp": "2026-06-01 10:00:00", "price": 100.0, "quantity": 10, "trade_type": "TRADE"},
            {"timestamp": "2026-06-01 10:01:00", "price": 101.0, "quantity": 12, "trade_type": "TRADE"},
            {"timestamp": "2026-06-01 10:02:00", "price": 120.0, "quantity": 8, "trade_type": "TRADE"},  # +20% spike
            {"timestamp": "2026-06-01 10:03:00", "price": 100.5, "quantity": 11, "trade_type": "TRADE"},
        ])
        result = engine.detect_intraday_shocks(ticks, daily_modal_price=100.0)

        assert result["is_shock"] is True
        assert len(result["shocks"]) > 0


class TestDecisionAgent:
    """Tests for DecisionAgent."""

    def test_get_signal(self, sample_forecast_df):
        """Test decision signal generation."""
        from agents.decision_support import DecisionAgent

        agent = DecisionAgent()
        risk_info = {"risk_score": 30, "risk_level": "Moderate"}
        shock_info = {"is_shock": False}

        result = agent.get_signal(2500, sample_forecast_df, risk_info, shock_info)

        assert "signal" in result
        assert result["signal"] in ("SELL NOW", "HOLD", "ACCUMULATE", "WAIT / RISKY", "NEUTRAL")

    def test_simulate_profit(self, sample_forecast_df):
        """Test profit simulation."""
        from agents.decision_support import DecisionAgent

        agent = DecisionAgent()
        result = agent.simulate_profit(2500, sample_forecast_df, qty=10)

        assert isinstance(result, pd.DataFrame)
