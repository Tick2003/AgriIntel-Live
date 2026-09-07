"""
database/__init__.py — Public API
===================================
Re-exports all database functions for convenience.
Supports both:
  - `from database import save_prices`
  - `import database.db_manager as db_manager`
"""

# Connection & Init
# Auth
from database.auth_db import get_org_details, get_user_by_email
from database.connection import DB_NAME, get_connection, init_db

# ETL Pipeline
from database.etl_db import (
    get_recent_quality_alerts,
    get_scraper_stats,
    log_quality_issues,
    log_scraper_execution,
    save_raw_prices,
)

# Forecasts & Metrics
from database.forecasts import (
    get_forecast_vs_actuals,
    get_performance_history,
    log_forecast,
    log_model_metrics,
)

# Market Prices
from database.prices import (
    export_prices_to_csv,
    get_latest_prices,
    get_price_history,
    get_state_level_aggregation,
    get_unique_items,
    import_prices_from_csv,
    save_prices,
)

# Real-Time / Intraday
from database.realtime import (
    clear_old_intraday_trades,
    get_ensemble_weight_history,
    get_latest_intraday_trades,
    log_ensemble_weights,
    save_intraday_trade,
)

# Signals
from database.signals import get_signal_stats, log_signal

# System, News, Weather
from database.system import (
    get_last_update,
    get_latest_news,
    get_weather_logs,
    log_system_event,
    save_news,
    save_weather,
    set_last_update,
)
