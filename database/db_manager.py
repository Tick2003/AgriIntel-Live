"""
database/db_manager.py — Backward-Compatible Re-Export Shim
=============================================================
All functions have been split into domain-focused modules:
  - database.connection  — get_connection(), init_db(), DB_NAME
  - database.prices      — save_prices(), get_latest_prices(), etc.
  - database.auth_db     — get_user_by_email(), get_org_details()
  - database.signals     — log_signal(), get_signal_stats()
  - database.forecasts   — log_forecast(), log_model_metrics(), etc.
  - database.etl_db      — save_raw_prices(), log_quality_issues(), etc.
  - database.system      — log_system_event(), save_news(), get_weather_logs(), etc.
  - database.realtime    — save_intraday_trade(), log_ensemble_weights(), etc.

This file re-exports everything so existing ``import database.db_manager as db_manager``
continues to work without changes.
"""

# --- Connection & Init ---
# --- Auth ---
from database.auth_db import get_org_details, get_user_by_email
from database.connection import DB_NAME, get_connection, init_db

# --- ETL Pipeline ---
from database.etl_db import (
    get_recent_quality_alerts,
    get_scraper_stats,
    log_quality_issues,
    log_scraper_execution,
    save_raw_prices,
)

# --- Forecasts & Metrics ---
from database.forecasts import (
    get_forecast_vs_actuals,
    get_performance_history,
    log_forecast,
    log_model_metrics,
)

# --- Market Prices ---
from database.prices import (
    export_prices_to_csv,
    get_latest_prices,
    get_price_history,
    get_state_level_aggregation,
    get_unique_items,
    import_prices_from_csv,
    save_prices,
)

# --- Real-Time / Intraday ---
from database.realtime import (
    clear_old_intraday_trades,
    get_ensemble_weight_history,
    get_latest_intraday_trades,
    log_ensemble_weights,
    save_intraday_trade,
)

# --- Signals ---
from database.signals import get_signal_stats, log_signal

# --- System, News, Weather ---
from database.system import (
    get_last_update,
    get_latest_news,
    get_weather_logs,
    log_system_event,
    save_news,
    save_weather,
    set_last_update,
)

__all__ = [
    # connection
    "DB_NAME", "get_connection", "init_db",
    # prices
    "save_prices", "get_latest_prices", "get_price_history", "get_unique_items",
    "get_state_level_aggregation", "export_prices_to_csv", "import_prices_from_csv",
    # auth
    "get_user_by_email", "get_org_details",
    # signals
    "log_signal", "get_signal_stats",
    # forecasts
    "log_forecast", "log_model_metrics", "get_performance_history", "get_forecast_vs_actuals",
    # etl
    "save_raw_prices", "log_quality_issues", "log_scraper_execution",
    "get_scraper_stats", "get_recent_quality_alerts",
    # system
    "log_system_event", "get_last_update", "set_last_update",
    "save_news", "get_latest_news", "save_weather", "get_weather_logs",
    # realtime
    "save_intraday_trade", "get_latest_intraday_trades", "clear_old_intraday_trades",
    "log_ensemble_weights", "get_ensemble_weight_history",
]


if __name__ == "__main__":
    init_db()
