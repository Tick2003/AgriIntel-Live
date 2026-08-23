"""
AgriIntel Test Configuration & Shared Fixtures
================================================
"""

import os
import sys
import pytest
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment
os.environ["AGRIINTEL_ENV"] = "test"
os.environ["AGRIINTEL_DB_NAME"] = "test_agri_intel.db"
os.environ["DEFAULT_ADMIN_EMAIL"] = "testadmin@agriintel.in"
os.environ["DEFAULT_ADMIN_PASSWORD"] = "testpass123"


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Initialize a clean test database for the entire test session."""
    db_path = "test_agri_intel.db"
    
    # Remove old test DB
    if os.path.exists(db_path):
        os.remove(db_path)
    
    import database.db_manager as dbm
    dbm.DB_NAME = db_path
    dbm.init_db()
    
    yield dbm
    
    # Cleanup after all tests
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except OSError:
        pass


@pytest.fixture
def db_manager():
    """Provide a db_manager instance pointed at the test DB."""
    import database.db_manager as dbm
    dbm.DB_NAME = "test_agri_intel.db"
    return dbm


@pytest.fixture
def sample_price_df():
    """Generate a sample 90-day price DataFrame for testing."""
    np.random.seed(42)
    dates = pd.date_range(end=datetime.today().date(), periods=90)
    base_price = 2500
    prices = [base_price]
    for _ in range(89):
        prices.append(prices[-1] + np.random.normal(0, 50))
    
    return pd.DataFrame({
        "date": dates,
        "commodity": "Onion",
        "mandi": "Azadpur",
        "price_min": [p - 100 for p in prices],
        "price_max": [p + 100 for p in prices],
        "price_modal": prices,
        "arrival": np.random.randint(50, 500, 90),
    })


@pytest.fixture
def sample_price_df_with_price_col(sample_price_df):
    """Sample DataFrame with 'price' column (app format)."""
    df = sample_price_df.copy()
    df = df.rename(columns={"price_modal": "price"})
    return df


@pytest.fixture
def sample_forecast_df():
    """Generate a sample 30-day forecast DataFrame."""
    np.random.seed(42)
    last_date = datetime.today()
    dates = [last_date + timedelta(days=i) for i in range(1, 31)]
    base = 2500
    forecasts = base + np.cumsum(np.random.normal(0, 30, 30))
    
    return pd.DataFrame({
        "date": dates,
        "forecast_price": forecasts,
        "lower_bound": forecasts - 200,
        "upper_bound": forecasts + 200,
        "commodity": "Onion",
        "mandi": "Azadpur",
    })


@pytest.fixture
def sample_news_df():
    """Generate sample news data."""
    return pd.DataFrame({
        "date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "title": ["Onion prices surge", "Wheat harvest good", "Rain forecast"],
        "source": ["Reuters", "ET", "IMD"],
        "url": ["https://example.com/1", "https://example.com/2", "https://example.com/3"],
        "sentiment": ["Negative", "Positive", "Neutral"],
    })


@pytest.fixture
def sample_weather_df():
    """Generate sample weather data."""
    return pd.DataFrame({
        "date": ["2026-01-01"],
        "region": "Azadpur",
        "temperature": [35.0],
        "rainfall": [0.0],
        "condition": ["Clear"],
        "wind_speed": [10.0],
        "humidity": [60.0],
    })


@pytest.fixture
def sample_intraday_df():
    """Generate sample intraday trade data."""
    now = datetime.now()
    trades = []
    for i in range(20):
        ts = (now - timedelta(minutes=20-i)).strftime("%Y-%m-%d %H:%M:%S.000")
        trades.append({
            "timestamp": ts,
            "commodity": "Onion",
            "mandi": "Azadpur",
            "price": 2500 + np.random.uniform(-50, 50),
            "quantity": np.random.uniform(5, 30),
            "trade_type": np.random.choice(["BID", "ASK", "TRADE"]),
        })
    return pd.DataFrame(trades)
