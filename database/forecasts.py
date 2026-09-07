"""
database/forecasts.py — Forecast & Model Metrics Logging
==========================================================
"""

import logging

import pandas as pd

from database.connection import get_connection

logger = logging.getLogger(__name__)


def log_forecast(gen_date, commodity, mandi, forecast_df):
    """
    Logs generated forecasts to DB for future accuracy checking.
    forecast_df must have ['date', 'forecast_price'] columns.
    """
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
        logger.error(f"Failed to log forecast: {e}")


def log_model_metrics(date, commodity, mandi, mape, rmse, mae, health_score, accuracy, sample_size):
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
        logger.error(f"Failed to log metrics: {e}")


def get_performance_history(commodity, mandi):
    """Retrieves historical performance metrics."""
    try:
        with get_connection() as conn:
            df = pd.read_sql("SELECT * FROM model_metrics WHERE commodity=? AND mandi=? ORDER BY date", conn, params=[commodity, mandi])
            return df
    except Exception as e:
        logger.error(f"get_performance_history failed: {e}")
        return pd.DataFrame()


def get_forecast_vs_actuals(commodity, mandi):
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
        logger.error(f"get_forecast_vs_actuals failed: {e}")
        return pd.DataFrame()

    if not df.empty:
        df['error'] = df['predicted_price'] - df['actual_price']
        df['error_pct'] = (df['error'].abs() / df['actual_price']) * 100

    return df
