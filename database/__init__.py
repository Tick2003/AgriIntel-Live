"""
database/__init__.py — Public API
===================================
Re-exports all database functions for convenience.
Supports both:
  - `from database import save_prices`
  - `import database.db_manager as db_manager`
"""

# Connection & Init
from database.connection import get_connection, init_db, DB_NAME

# Market Prices
from database.prices import (
    save_prices,
    get_latest_prices,
    get_price_history,
    get_unique_items,
    get_state_level_aggregation,
    export_prices_to_csv,
    import_prices_from_csv,
)

# Auth
from database.auth_db import get_user_by_email, get_org_details

# Signals
from database.signals import log_signal, get_signal_stats

# Forecasts & Metrics
from database.forecasts import (
    log_forecast,
    log_model_metrics,
    get_performance_history,
    get_forecast_vs_actuals,
)

# ETL Pipeline
from database.etl_db import (
    save_raw_prices,
    log_quality_issues,
    log_scraper_execution,
    get_scraper_stats,
    get_recent_quality_alerts,
)

# System, News, Weather
from database.system import (
    log_system_event,
    get_last_update,
    set_last_update,
    save_news,
    get_latest_news,
    save_weather,
    get_weather_logs,
)

# Real-Time / Intraday
from database.realtime import (
    save_intraday_trade,
    get_latest_intraday_trades,
    clear_old_intraday_trades,
    log_ensemble_weights,
    get_ensemble_weight_history,
)
