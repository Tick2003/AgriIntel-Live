"""
database/system.py — System Logs, App Metadata, News & Weather
================================================================
"""

import pandas as pd
import logging
from datetime import datetime

from database.connection import get_connection

logger = logging.getLogger(__name__)


# --- System Events ---

def log_system_event(level, source, message, metadata=""):
    """Logs a system event to the database."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO system_logs (timestamp, level, source, message, metadata) VALUES (?, ?, ?, ?, ?)",
                      (timestamp, level, source, message, str(metadata)))
            conn.commit()
    except Exception as e:
        logger.error(f"System event logging failed: {e}")


# --- App Metadata ---

def get_last_update():
    """Retrieve the last update timestamp from app_metadata."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT value FROM app_metadata WHERE key = 'last_update'")
            result = c.fetchone()
            return result[0] if result else None
    except Exception as e:
        logger.debug(f"get_last_update failed: {e}")
        return None


def set_last_update():
    """Set the last update timestamp in app_metadata to the current time."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT OR REPLACE INTO app_metadata (key, value) VALUES ('last_update', ?)", (now_str,))
            conn.commit()
    except Exception as e:
        logger.error(f"set_last_update failed: {e}")


# --- News ---

def save_news(df):
    """Save news to DB, avoiding duplicates."""
    if df.empty:
        return

    try:
        with get_connection() as conn:
            # 1. Get existing titles
            try:
                existing_titles = pd.read_sql("SELECT title FROM news_alerts", conn)['title'].tolist()
                existing_titles = set(existing_titles)
            except Exception:
                existing_titles = set()

            # 2. Filter new items
            if 'title' in df.columns:
                # Deduplicate input df first
                df = df.drop_duplicates(subset=['title'])
                # Filter against DB
                new_df = df[~df['title'].isin(existing_titles)]
                
                if not new_df.empty:
                    new_df.to_sql('news_alerts', conn, if_exists='append', index=False)
                    logger.info(f"Added {len(new_df)} new news items.")
                else:
                    logger.info("No new unique news items found.")
    except Exception as e:
        logger.error(f"save_news failed: {e}")


def get_latest_news():
    """Get latest news."""
    try:
        with get_connection() as conn:
            df = pd.read_sql("SELECT * FROM news_alerts ORDER BY date DESC LIMIT 20", conn)
            return df
    except Exception as e:
        logger.error(f"get_latest_news failed: {e}")
        return pd.DataFrame()


# --- Weather ---

def save_weather(df):
    """Save weather logs."""
    try:
        with get_connection() as conn:
            df.to_sql('weather_logs', conn, if_exists='append', index=False)
    except Exception as e:
        logger.error(f"save_weather failed: {e}")


def get_weather_logs(region=None):
    """Get weather logs."""
    try:
        with get_connection() as conn:
            query = "SELECT * FROM weather_logs"
            params = []
            if region:
                query += " WHERE region = ?"
                params.append(region)
            df = pd.read_sql(query, conn, params=params)
            return df
    except Exception as e:
        logger.error(f"get_weather_logs failed: {e}")
        return pd.DataFrame()
