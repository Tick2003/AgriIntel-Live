"""
database/forecasts.py — Forecast & Model Metrics Logging
==========================================================
"""

import logging

import pandas as pd

from database.connection import get_connection

logger = logging.getLogger(__name__)


def log_forecast(gen_date: str, commodity: str, mandi: str, forecast_df: pd.DataFrame) -> None:
    """
    Logs generated forecasts to DB for future accuracy checking.
    forecast_df must have ['date', 'forecast_price'] columns.
    """
    if forecast_df is None or forecast_df.empty:
        return
    try:
        with get_connection() as conn:
            c = conn.cursor()

            # Batch insert
            data_to_insert = []
            for _, row in forecast_df.iterrows():
                target_date = row['date'].strftime("%Y-%m-%d") if isinstance(row['date'], pd.Timestamp) else row['date']
                data_to_insert.append((
                    gen_date, target_date, commodity, mandi, row['forecast_price']
                ))

            c.executemany('''
                INSERT INTO forecast_logs (gen_date, target_date, commodity, mandi, predicted_price)
                VALUES (?, ?, ?, ?, ?)
            ''', data_to_insert)

            conn.commit()
    except Exception as e:
        logger.error("Failed to log forecast for %s/%s: %s", commodity, mandi, e)


def log_model_metrics(
    date: str,
    commodity: str,
    mandi: str,
    mape: float,
    rmse: float,
    mae: float,
    health_score: float,
    accuracy: float,
    sample_size: int,
) -> None:
    """Logs calculated performance metrics."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO model_metrics (date, commodity, mandi, mape, rmse, mae, health_score, signal_accuracy, sample_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (date, commodity, mandi, mape, rmse, mae, health_score, accuracy, sample_size))
            conn.commit()
    except Exception as e:
        logger.error("Failed to log metrics for %s/%s: %s", commodity, mandi, e)


def get_performance_history(commodity: str, mandi: str) -> pd.DataFrame:
    """Retrieves historical performance metrics."""
    try:
        with get_connection() as conn:
            df = pd.read_sql("SELECT * FROM model_metrics WHERE commodity=? AND mandi=? ORDER BY date", conn, params=[commodity, mandi])
            return df
    except Exception as e:
        logger.error("get_performance_history failed for %s/%s: %s", commodity, mandi, e)
        return pd.DataFrame()


def get_forecast_vs_actuals(commodity: str, mandi: str) -> pd.DataFrame:
    """
    Joins forecast logs with actual market prices to compare.
    Returns DF with [target_date, predicted_price, actual_price, error, error_pct]
    """
    try:
        with get_connection() as conn:
            query = '''
                SELECT
                    f.target_date,
                    f.predicted_price,
                    m.price_modal as actual_price,
                    f.gen_date
                FROM forecast_logs f
                JOIN market_prices m ON f.target_date = m.date AND f.commodity = m.commodity AND f.mandi = m.mandi
                WHERE f.commodity = ? AND f.mandi = ?
                ORDER BY f.target_date
            '''
            df = pd.read_sql(query, conn, params=[commodity, mandi])
    except Exception as e:
        logger.error("get_forecast_vs_actuals failed for %s/%s: %s", commodity, mandi, e)
        return pd.DataFrame()

    if not df.empty:
        df['error'] = df['predicted_price'] - df['actual_price']
        df['error_pct'] = (df['error'].abs() / df['actual_price']) * 100

    return df

