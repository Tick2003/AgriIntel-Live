"""
Edge-Case & Hardening Tests
=================================
Tests for boundary conditions, invalid inputs, and failure modes
that are NOT covered by the existing test suite.

These tests verify that the hardened code handles degenerate inputs
without crashing — the same way the production code path does.
"""

import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─── Config Hardening ──────────────────────────────────────────────────────

class TestConfigHardening:
    """Tests for crash-proof config parsing."""

    def test_safe_int_with_garbage_env(self, monkeypatch):
        """Bad env var should fall back to default, not crash."""
        monkeypatch.setenv("CACHE_TTL", "not_a_number")
        # Re-import to trigger __post_init__
        from config import _safe_int
        result = _safe_int("CACHE_TTL", 600)
        assert result == 600

    def test_safe_int_with_valid_env(self, monkeypatch):
        """Valid env var should parse correctly."""
        monkeypatch.setenv("CACHE_TTL", "1200")
        from config import _safe_int
        result = _safe_int("CACHE_TTL", 600)
        assert result == 1200

    def test_safe_int_with_empty_env(self):
        """Missing env var should use default."""
        from config import _safe_int
        result = _safe_int("NONEXISTENT_VAR_12345", 42)
        assert result == 42

    def test_safe_bool_true_values(self, monkeypatch):
        """Various truthy strings should parse as True."""
        from config import _safe_bool
        for val in ["true", "True", "TRUE", "1", "yes", "YES"]:
            monkeypatch.setenv("TEST_BOOL", val)
            assert _safe_bool("TEST_BOOL", False) is True

    def test_safe_bool_false_values(self, monkeypatch):
        """Non-truthy strings should parse as False."""
        from config import _safe_bool
        for val in ["false", "0", "no", "maybe", ""]:
            monkeypatch.setenv("TEST_BOOL", val)
            # Empty string returns default
            if val == "":
                assert _safe_bool("TEST_BOOL", False) is False
            else:
                assert _safe_bool("TEST_BOOL", True) is False

    def test_settings_singleton_has_defaults(self):
        """Settings singleton should load with valid defaults."""
        from config import settings
        assert settings.app.environment in ("development", "test", "staging", "production")
        assert settings.db.pool_size >= 1
        assert settings.security.session_timeout_hours >= 1


# ─── Database Write Edge Cases ─────────────────────────────────────────────

class TestDatabaseWriteEdgeCases:
    """Tests for boundary conditions on database write functions."""

    def test_save_prices_with_none(self, db_manager):
        """save_prices(None) should not crash."""
        db_manager.save_prices(None)  # Should return silently

    def test_save_prices_with_empty_df(self, db_manager):
        """save_prices(empty) should not crash."""
        db_manager.save_prices(pd.DataFrame())

    def test_save_prices_with_nan_values(self, db_manager):
        """DataFrame with NaN in non-critical columns should save."""
        df = pd.DataFrame({
            "date": ["2026-06-01"],
            "commodity": ["Onion"],
            "mandi": ["Azadpur"],
            "price_min": [np.nan],
            "price_max": [np.nan],
            "price_modal": [2500.0],
            "arrival": [np.nan],
        })
        db_manager.save_prices(df)  # Should not raise

    def test_save_prices_with_null_critical_columns(self, db_manager):
        """Rows with NULL commodity/mandi should be dropped, not crash."""
        df = pd.DataFrame({
            "date": ["2026-06-01", "2026-06-02"],
            "commodity": ["Onion", None],
            "mandi": ["Azadpur", "Pune"],
            "price_modal": [2500.0, 2600.0],
        })
        # Should save only the valid row, not crash
        db_manager.save_prices(df)

    def test_save_news_with_none(self, db_manager):
        """save_news(None) should not crash."""
        db_manager.save_news(None)

    def test_save_weather_with_none(self, db_manager):
        """save_weather(None) should not crash."""
        db_manager.save_weather(None)

    def test_save_raw_prices_with_none(self, db_manager):
        """save_raw_prices(None) should not crash."""
        db_manager.save_raw_prices(None, "BATCH_NULL")

    def test_log_quality_issues_empty_list(self, db_manager):
        """log_quality_issues([]) should be a no-op."""
        db_manager.log_quality_issues([])

    def test_log_forecast_with_none_df(self, db_manager):
        """log_forecast(None) should not crash."""
        from database.forecasts import log_forecast
        log_forecast("2026-06-01", "Onion", "Azadpur", None)

    def test_log_forecast_with_empty_df(self, db_manager):
        """log_forecast(empty) should not crash."""
        from database.forecasts import log_forecast
        log_forecast("2026-06-01", "Onion", "Azadpur", pd.DataFrame())


# ─── Database Read Edge Cases ──────────────────────────────────────────────

class TestDatabaseReadEdgeCases:
    """Tests for boundary conditions on database read functions."""

    def test_get_price_history_nonexistent(self, db_manager):
        """Querying non-existent commodity/mandi returns empty DF."""
        df = db_manager.get_price_history("NoSuchCrop", "NoSuchMandi")
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_get_signal_stats_nonexistent(self, db_manager):
        """Signal stats for non-existent pair returns zeroed dict."""
        stats = db_manager.get_signal_stats("NoSuchCrop", "NoSuchMandi")
        assert stats["total"] == 0
        assert stats["win_rate"] == 0

    def test_get_weather_logs_no_region(self, db_manager):
        """Weather logs without region filter returns all."""
        df = db_manager.get_weather_logs()
        assert isinstance(df, pd.DataFrame)

    def test_get_forecast_vs_actuals_nonexistent(self, db_manager):
        """Forecast vs actuals for non-existent pair returns empty DF."""
        df = db_manager.get_forecast_vs_actuals("NoSuchCrop", "NoSuchMandi")
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_get_ensemble_weight_history_nonexistent(self, db_manager):
        """Ensemble weights for non-existent pair returns empty DF."""
        df = db_manager.get_ensemble_weight_history("NoSuchCrop", "NoSuchMandi")
        assert isinstance(df, pd.DataFrame)
        assert df.empty


# ─── Agent Edge Cases ──────────────────────────────────────────────────────

class TestAgentEdgeCases:
    """Tests for agents with degenerate inputs."""

    def test_forecast_with_constant_prices(self):
        """XGBoost should handle zero-variance data without crash."""
        from agents.forecast_execution import ForecastingAgent

        agent = ForecastingAgent()
        df = pd.DataFrame({
            "date": pd.date_range(end=datetime.today(), periods=90),
            "price": [2500.0] * 90,  # Zero variance
            "arrival": [100] * 90,
        })
        result = agent.generate_forecasts(df, "Potato", "Agra")
        assert not result.empty
        assert len(result) == 30

    def test_risk_score_with_nan_volatility(self):
        """Risk engine should handle NaN volatility gracefully."""
        from agents.risk_scoring import MarketRiskEngine

        engine = MarketRiskEngine()
        # NaN volatility — can happen with pct_change().std() on constant data
        result = engine.calculate_risk_score(
            shock_info={"is_shock": False},
            forecast_std=0.0,
            market_volatility=float('nan'),
        )
        assert "risk_score" in result
        assert 0 <= result["risk_score"] <= 100

    def test_risk_score_with_zero_inputs(self):
        """Risk engine should work with all-zero inputs."""
        from agents.risk_scoring import MarketRiskEngine

        engine = MarketRiskEngine()
        result = engine.calculate_risk_score(
            shock_info={"is_shock": False},
            forecast_std=0.0,
            market_volatility=0.0,
        )
        assert result["risk_score"] == 0
        assert result["risk_level"] == "Stable"

    def test_decision_agent_with_empty_forecast(self):
        """Decision agent should handle empty forecast gracefully."""
        from agents.decision_support import DecisionAgent

        agent = DecisionAgent()
        result = agent.get_signal(
            2500,
            pd.DataFrame(),
            {"risk_score": 50, "risk_level": "Moderate"},
            {"is_shock": False},
        )
        assert result["signal"] == "NEUTRAL"

    def test_decision_agent_simulate_profit_empty(self):
        """Profit simulation with empty forecast returns empty DF."""
        from agents.decision_support import DecisionAgent

        agent = DecisionAgent()
        result = agent.simulate_profit(2500, pd.DataFrame())
        assert isinstance(result, pd.DataFrame)
        assert result.empty


# ─── Connection Pool Edge Cases ────────────────────────────────────────────

class TestConnectionPoolHardening:
    """Tests for the hardened connection pool."""

    def test_auto_commit_on_success(self, db_manager):
        """Data should persist even without explicit conn.commit()."""
        from database.connection import get_connection

        # Write without explicit commit — auto-commit should handle it
        with get_connection() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO system_logs (timestamp, level, source, message, metadata) "
                "VALUES (?, ?, ?, ?, ?)",
                ("2026-06-01 00:00:00", "INFO", "TEST_AUTOCOMMIT", "autocommit test", ""),
            )
            # NOTE: no conn.commit() here!

        # Read back on a fresh connection
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM system_logs WHERE source = 'TEST_AUTOCOMMIT'")
            row = c.fetchone()
        assert row is not None, "Auto-commit failed: data was lost"

    def test_rollback_on_exception(self, db_manager):
        """Data should NOT persist when an exception occurs."""
        from database.connection import get_connection

        with pytest.raises(RuntimeError):
            with get_connection() as conn:
                c = conn.cursor()
                c.execute(
                    "INSERT INTO system_logs (timestamp, level, source, message, metadata) "
                    "VALUES (?, ?, ?, ?, ?)",
                    ("2026-06-01 00:00:00", "INFO", "TEST_ROLLBACK", "rollback test", ""),
                )
                raise RuntimeError("Deliberate failure")

        # Should NOT be in DB
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM system_logs WHERE source = 'TEST_ROLLBACK'")
            row = c.fetchone()
        assert row is None, "Rollback failed: data persisted despite exception"

    def test_sequential_connections_isolated(self, db_manager):
        """Sequential get_connection() calls should be isolated."""
        from database.connection import get_connection

        for i in range(5):
            with get_connection() as conn:
                conn.cursor().execute("SELECT 1")


# ─── Exception Hierarchy ──────────────────────────────────────────────────

class TestExceptionHierarchy:
    """Tests for the domain exception module."""

    def test_all_exceptions_are_subclass_of_base(self):
        """All domain exceptions should inherit from AgriIntelDBError."""
        from database.exceptions import (
            AgriIntelDBError,
            ConnectionError,
            DataValidationError,
            MigrationError,
            QueryError,
        )
        for exc_cls in [ConnectionError, DataValidationError, QueryError, MigrationError]:
            assert issubclass(exc_cls, AgriIntelDBError)

    def test_data_validation_error_has_fields(self):
        """DataValidationError should carry field and detail info."""
        from database.exceptions import DataValidationError

        exc = DataValidationError("bad data", field="price", detail="negative value")
        assert exc.field == "price"
        assert exc.detail == "negative value"
        assert "bad data" in str(exc)
