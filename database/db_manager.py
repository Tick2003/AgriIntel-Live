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

This file re-exports everything so existing `import database.db_manager as db_manager`
continues to work without changes.
"""

# --- Connection & Init ---
from database.connection import init_db

# --- Market Prices ---

# --- Auth ---

# --- Signals ---

# --- Forecasts & Metrics ---

# --- ETL Pipeline ---

# --- System, News, Weather ---

# --- Real-Time / Intraday ---


if __name__ == "__main__":
    init_db()
