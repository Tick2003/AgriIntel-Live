"""
database/etl_db.py — ETL Pipeline Database Operations
=======================================================
Raw staging data, quality logs, and scraper execution stats.
"""

import logging
from datetime import datetime

import pandas as pd

from database.connection import get_connection

logger = logging.getLogger(__name__)


def save_raw_prices(df: pd.DataFrame, batch_id: str) -> None:
    """Saves incoming scraped data to the raw staging table."""
    if df is None or df.empty:
        return
    try:
        with get_connection() as conn:
            # Add metadata columns
            df_copy = df.copy()
            df_copy['batch_id'] = batch_id
            df_copy['ingestion_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df_copy['status'] = 'PENDING'

            df_copy.to_sql('raw_mandi_prices', conn, if_exists='append', index=False)
    except Exception as e:
        logger.error("save_raw_prices failed for batch %s: %s", batch_id, e)


def log_quality_issues(issues_list: list[dict]) -> None:
    """
    Logs data quality issues.
    issues_list: List of dicts {batch_id, date, commodity, mandi, issue_type, severity, details, raw_value}
    """
    if not issues_list:
        return
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.executemany('''
                INSERT INTO data_quality_logs (batch_id, date, commodity, mandi, issue_type, severity, details, raw_value)
                VALUES (:batch_id, :date, :commodity, :mandi, :issue_type, :severity, :details, :raw_value)
            ''', issues_list)
            conn.commit()
    except Exception as e:
        logger.error("log_quality_issues failed: %s", e)


def log_scraper_execution(
    status: str,
    duration: float,
    fetched: int,
    validated: int,
    rejected: int,
    error_msg: str = "",
) -> None:
    """Logs the execution summary of the scraper run."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute('''
                INSERT INTO scraper_execution_stats (timestamp, status, duration_seconds, records_fetched, records_validated, records_rejected, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, status, duration, fetched, validated, rejected, error_msg))
            conn.commit()
    except Exception as e:
        logger.error("log_scraper_execution failed: %s", e)


def get_scraper_stats(limit: int = 30) -> tuple[pd.DataFrame, float]:
    """Fetch scraper stats for dashboard."""
    try:
        with get_connection() as conn:
            df = pd.read_sql("SELECT * FROM scraper_execution_stats ORDER BY timestamp DESC LIMIT ?", conn, params=[limit])

            # Calculate Success Rate
            success_rate = 0.0
            if not df.empty:
                success_count = len(df[df['status'] == 'SUCCESS'])
                success_rate = (success_count / len(df)) * 100

            return df, success_rate
    except Exception as e:
        logger.error("get_scraper_stats failed: %s", e)
        return pd.DataFrame(), 0.0


def get_recent_quality_alerts(limit: int = 10) -> pd.DataFrame:
    """Fetches recent data quality alerts."""
    try:
        with get_connection() as conn:
            query = "SELECT * FROM data_quality_logs ORDER BY id DESC LIMIT ?"
            df = pd.read_sql(query, conn, params=[limit])
            return df
    except Exception as e:
        logger.debug("Quality alerts query failed (table may not exist): %s", e)
        return pd.DataFrame()

