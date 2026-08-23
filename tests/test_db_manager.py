"""
Unit Tests for database.db_manager
====================================
Covers all CRUD operations, migrations, and edge cases.
"""

import os
import sys
import pytest
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestInitDB:
    """Tests for database initialization and migrations."""

    def test_init_creates_all_tables(self, db_manager):
        """Verify all expected tables exist after init_db."""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
        
        expected_tables = {
            'market_prices', 'news_alerts', 'weather_logs', 'app_metadata',
            'signal_logs', 'user_config', 'system_logs', 'forecast_logs',
            'model_metrics', 'raw_mandi_prices', 'data_quality_logs',
            'scraper_execution_stats', 'organizations', 'users',
            'voice_call_logs', 'intraday_trades', 'ensemble_weights_log',
        }
        assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"

    def test_default_org_created(self, db_manager):
        """Verify default organization is created."""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM organizations")
            count = cursor.fetchone()[0]
        assert count >= 1

    def test_default_admin_created(self, db_manager):
        """Verify default admin user is created from env vars."""
        user = db_manager.get_user_by_email("testadmin@agriintel.in")
        assert user is not None
        assert user['role'] == 'Admin'


class TestPriceCRUD:
    """Tests for price data operations."""

    def test_save_and_retrieve_prices(self, db_manager, sample_price_df):
        """Test saving and retrieving market prices."""
        db_manager.save_prices(sample_price_df)
        
        df = db_manager.get_latest_prices("Onion")
        assert not df.empty
        assert "price_modal" in df.columns
        assert "Onion" in df['commodity'].values

    def test_get_latest_prices_no_commodity(self, db_manager):
        """Test retrieving all prices without filter."""
        df = db_manager.get_latest_prices()
        # Should return something (from previous test or init)
        assert isinstance(df, pd.DataFrame)

    def test_get_latest_prices_nonexistent(self, db_manager):
        """Test querying non-existent commodity returns empty."""
        df = db_manager.get_latest_prices("NonExistentCrop123")
        assert df.empty

    def test_get_price_history(self, db_manager):
        """Test price history with date range."""
        df = db_manager.get_price_history("Onion", "Azadpur")
        assert isinstance(df, pd.DataFrame)

    def test_get_unique_items_commodity(self, db_manager):
        """Test getting unique commodities."""
        items = db_manager.get_unique_items("commodity")
        assert isinstance(items, list)

    def test_get_unique_items_mandi(self, db_manager):
        """Test getting unique mandis."""
        items = db_manager.get_unique_items("mandi")
        assert isinstance(items, list)

    def test_get_unique_items_invalid_column(self, db_manager):
        """Test that invalid column name raises ValueError."""
        with pytest.raises(ValueError):
            db_manager.get_unique_items("INVALID; DROP TABLE users;--")


class TestNewsCRUD:
    """Tests for news data operations."""

    def test_save_and_retrieve_news(self, db_manager, sample_news_df):
        """Test saving and retrieving news."""
        db_manager.save_news(sample_news_df)
        
        df = db_manager.get_latest_news()
        assert not df.empty
        assert "title" in df.columns

    def test_save_news_deduplication(self, db_manager, sample_news_df):
        """Test that duplicate news items are not inserted."""
        db_manager.save_news(sample_news_df)
        db_manager.save_news(sample_news_df)  # Save again
        
        df = db_manager.get_latest_news()
        # Titles should be unique
        assert df['title'].nunique() == len(df)

    def test_save_empty_news(self, db_manager):
        """Test saving empty news DataFrame."""
        db_manager.save_news(pd.DataFrame())  # Should not raise


class TestWeatherCRUD:
    """Tests for weather data operations."""

    def test_save_and_retrieve_weather(self, db_manager, sample_weather_df):
        """Test saving and retrieving weather data."""
        db_manager.save_weather(sample_weather_df)
        
        df = db_manager.get_weather_logs()
        assert not df.empty

    def test_get_weather_by_region(self, db_manager):
        """Test filtering weather by region."""
        df = db_manager.get_weather_logs(region="Azadpur")
        assert isinstance(df, pd.DataFrame)


class TestMetadata:
    """Tests for app metadata operations."""

    def test_set_and_get_last_update(self, db_manager):
        """Test setting and getting last update timestamp."""
        db_manager.set_last_update()
        
        result = db_manager.get_last_update()
        assert result is not None
        # Should be parseable datetime
        datetime.strptime(result, "%Y-%m-%d %H:%M:%S")


class TestSignalLogging:
    """Tests for signal tracking."""

    def test_log_and_get_signal_stats(self, db_manager):
        """Test signal logging and stat retrieval."""
        db_manager.log_signal("2026-01-01", "Onion", "Azadpur", "HOLD", 2500)
        
        stats = db_manager.get_signal_stats("Onion", "Azadpur")
        assert isinstance(stats, dict)
        assert "total" in stats
        assert "win_rate" in stats

    def test_log_signal_deduplication(self, db_manager):
        """Test that duplicate signals are not inserted."""
        db_manager.log_signal("2026-01-01", "Onion", "Azadpur", "HOLD", 2500)
        db_manager.log_signal("2026-01-01", "Onion", "Azadpur", "SELL NOW", 2600)
        # Second should be ignored (same date/commodity/mandi)


class TestSystemLogs:
    """Tests for system event logging."""

    def test_log_system_event(self, db_manager):
        """Test system event logging."""
        db_manager.log_system_event("INFO", "TEST", "Test event logged", "metadata123")
        
        with db_manager.get_connection() as conn:
            df = pd.read_sql("SELECT * FROM system_logs WHERE source='TEST'", conn)
        assert not df.empty


class TestIntradayTrades:
    """Tests for real-time intraday trade operations."""

    def test_save_and_get_intraday_trade(self, db_manager):
        """Test saving and retrieving intraday trades."""
        trade = {
            "timestamp": "2026-06-14 10:00:00.000",
            "commodity": "Onion",
            "mandi": "Azadpur",
            "price": 2500.0,
            "quantity": 10.0,
            "trade_type": "TRADE",
        }
        db_manager.save_intraday_trade(trade)
        
        df = db_manager.get_latest_intraday_trades("Onion", "Azadpur", limit=5)
        assert not df.empty
        assert "price" in df.columns

    def test_clear_old_intraday_trades(self, db_manager):
        """Test clearing old trades."""
        # This should not raise
        db_manager.clear_old_intraday_trades(hours=0)


class TestDataReliability:
    """Tests for data reliability pipeline."""

    def test_save_raw_prices(self, db_manager, sample_price_df):
        """Test saving raw prices to staging table."""
        db_manager.save_raw_prices(sample_price_df, "TEST_BATCH_001")
        
        with db_manager.get_connection() as conn:
            df = pd.read_sql("SELECT * FROM raw_mandi_prices WHERE batch_id='TEST_BATCH_001'", conn)
        assert not df.empty

    def test_log_quality_issues(self, db_manager):
        """Test logging quality issues."""
        issues = [{
            "batch_id": "TEST_BATCH",
            "date": "2026-01-01",
            "commodity": "Onion",
            "mandi": "Azadpur",
            "issue_type": "OUTLIER",
            "severity": "WARNING",
            "details": "Price 50% above median",
            "raw_value": "9999",
        }]
        db_manager.log_quality_issues(issues)
        
        alerts = db_manager.get_recent_quality_alerts()
        assert not alerts.empty

    def test_log_scraper_execution(self, db_manager):
        """Test scraper execution logging."""
        db_manager.log_scraper_execution("SUCCESS", 12.5, 100, 95, 5)
        
        df, rate = db_manager.get_scraper_stats()
        assert not df.empty
        assert rate > 0


class TestConnectionPool:
    """Tests for connection pool behavior."""

    def test_get_connection_context_manager(self, db_manager):
        """Test that get_connection works as context manager."""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        assert result == (1,)

    def test_concurrent_connections(self, db_manager):
        """Test that multiple connections can work in sequence."""
        for _ in range(10):
            with db_manager.get_connection() as conn:
                conn.cursor().execute("SELECT 1")
