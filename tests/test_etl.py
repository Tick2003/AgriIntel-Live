"""
Unit Tests for ETL Pipeline
=============================
Tests data loading, validation, scraper, and simulation.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAgmarknetScraper:
    """Tests for the data fetching/scraper module."""

    def test_simulated_prices(self):
        """Test simulation fallback returns valid data."""
        from etl.agmarknet_scraper import fetch_simulated_prices
        
        df = fetch_simulated_prices()
        assert not df.empty
        assert len(df) > 0
        
        # Check schema
        expected_cols = {"date", "commodity", "mandi", "price_min", "price_max", "price_modal", "arrival"}
        assert expected_cols.issubset(set(df.columns))
        
        # Prices should be positive
        assert (df['price_modal'] > 0).all()
        assert (df['price_min'] >= 0).all()

    def test_simulated_prices_coverage(self):
        """Test that simulation covers all tracked commodities and markets."""
        from etl.agmarknet_scraper import fetch_simulated_prices, TRACKED_COMMODITIES, TRACKED_MARKETS
        
        df = fetch_simulated_prices()
        assert df['commodity'].nunique() == len(TRACKED_COMMODITIES)
        assert df['mandi'].nunique() == len(TRACKED_MARKETS)

    def test_get_api_key_from_env(self):
        """Test API key retrieval from environment."""
        from etl.agmarknet_scraper import _get_api_key
        
        # Without key set
        old_val = os.environ.pop("DATA_GOV_IN_API_KEY", None)
        result = _get_api_key()
        assert result == ""
        
        # With key set
        os.environ["DATA_GOV_IN_API_KEY"] = "test-key-123"
        result = _get_api_key()
        assert result == "test-key-123"
        
        # Restore
        if old_val:
            os.environ["DATA_GOV_IN_API_KEY"] = old_val
        else:
            os.environ.pop("DATA_GOV_IN_API_KEY", None)

    def test_get_all_commodities_data(self):
        """Test the cascading fetch returns data."""
        from etl.agmarknet_scraper import get_all_commodities_data
        
        # Without API key, should fall through to simulation
        old_val = os.environ.pop("DATA_GOV_IN_API_KEY", None)
        
        df = get_all_commodities_data()
        assert not df.empty
        assert "price_modal" in df.columns
        
        # Restore
        if old_val:
            os.environ["DATA_GOV_IN_API_KEY"] = old_val


class TestDataValidation:
    """Tests for data quality validation in the ETL pipeline."""

    def test_price_range_validation(self):
        """Test that prices are within reasonable ranges."""
        from etl.agmarknet_scraper import fetch_simulated_prices
        
        df = fetch_simulated_prices()
        
        # No negative prices
        assert (df['price_modal'] >= 0).all()
        
        # Min <= Modal <= Max
        assert (df['price_min'] <= df['price_modal']).all()
        assert (df['price_modal'] <= df['price_max']).all()

    def test_date_format(self):
        """Test that dates are in correct format."""
        from etl.agmarknet_scraper import fetch_simulated_prices
        
        df = fetch_simulated_prices()
        # All dates should be parseable
        dates = pd.to_datetime(df['date'], errors='coerce')
        assert dates.notna().all()


class TestRealtimeStream:
    """Tests for the real-time tick stream module."""

    def test_stream_status_default(self):
        """Test default stream status."""
        from etl.realtime_stream import get_stream_status
        
        status = get_stream_status()
        assert "is_running" in status
        assert isinstance(status["is_running"], bool)

    def test_get_order_book_empty(self):
        """Test order book with no data returns empty structure."""
        from etl.realtime_stream import get_order_book
        
        result = get_order_book("NonExistent", "FakeMandi")
        assert "bids" in result
        assert "asks" in result
        assert isinstance(result["bids"], pd.DataFrame)
        assert isinstance(result["asks"], pd.DataFrame)

    def test_get_intraday_trades_empty(self):
        """Test intraday trades with no data."""
        from etl.realtime_stream import get_intraday_trades
        
        result = get_intraday_trades("NonExistent", "FakeMandi")
        assert isinstance(result, pd.DataFrame)


class TestConfig:
    """Tests for centralized configuration."""

    def test_config_loads(self):
        """Test that config module loads without error."""
        from config import settings
        
        assert settings.app.environment in ("development", "test", "production", "staging")
        assert isinstance(settings.db.name, str)
        assert isinstance(settings.security.session_timeout_hours, int)
        assert isinstance(settings.etl.staleness_threshold_hours, int)

    def test_config_environment_detection(self):
        """Test environment detection."""
        from config import settings
        
        # We set AGRIINTEL_ENV=test in conftest
        assert not settings.app.is_production
