"""
database/prices.py — Market Price CRUD Operations
===================================================
"""

import pandas as pd
import logging
from datetime import datetime

from database.connection import get_connection, DB_NAME

logger = logging.getLogger(__name__)


def save_prices(df):
    """Save a pandas DataFrame of prices to the DB."""
    with get_connection() as conn:
        # Filter for valid columns only
        valid_cols = ['date', 'commodity', 'mandi', 'price_min', 'price_max', 'price_modal', 'arrival']
        # Add optional unit if present, else it defaults in DB
        if 'unit' in df.columns:
            valid_cols.append('unit')
            
        # Only keep columns that are in df
        cols_to_save = [col for col in valid_cols if col in df.columns]
        
        df_clean = df[cols_to_save].copy()
        
        df_clean.to_sql('market_prices', conn, if_exists='append', index=False)
        logger.info(f"Saved {len(df_clean)} price records.")


def get_latest_prices(commodity=None):
    """Retrieve prices from the DB."""
    try:
        with get_connection() as conn:
            query = "SELECT * FROM market_prices"
            params = []
            if commodity:
                query += " WHERE commodity = ?"
                params.append(commodity)
            df = pd.read_sql(query, conn, params=params)
            return df
    except Exception as e:
        logger.error(f"get_latest_prices failed: {e}")
        return pd.DataFrame()


def get_price_history(commodity, mandi, start_date=None, end_date=None):
    """Fetches historical prices for a specific market within a date range."""
    try:
        with get_connection() as conn:
            query = "SELECT * FROM market_prices WHERE commodity=? AND mandi=?"
            params = [commodity, mandi]
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
                
            query += " ORDER BY date ASC"
            
            df = pd.read_sql(query, conn, params=params)
            return df
    except Exception as e:
        logger.error(f"get_price_history failed: {e}")
        return pd.DataFrame()


def get_unique_items(column):
    """Get distinct values for a column (commodity/mandi)."""
    if column not in ['commodity', 'mandi']:
        raise ValueError("Invalid column name for get_unique_items")
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Safe: column is validated against whitelist above
            cursor.execute(f"SELECT DISTINCT {column} FROM market_prices ORDER BY {column}")
            items = [row[0] for row in cursor.fetchall()]
            return items
    except Exception as e:
        logger.error(f"get_unique_items failed for {column}: {e}")
        return []


def get_state_level_aggregation():
    """
    Aggregates data by State (derived from Mandi location or Mock map).
    Returns DF with State, Volatility, PriceChange.
    """
    try:
        with get_connection() as conn:
            df = pd.read_sql("SELECT commodity, mandi, price_modal, date FROM market_prices", conn)
    except Exception as e:
        logger.error(f"State aggregation query failed: {e}")
        return pd.DataFrame()
    
    if df.empty: return pd.DataFrame()
    
    mandi_state_map = {
        "Azadpur": "Delhi", "Pune": "Maharashtra", "Lasalgaon": "Maharashtra",
        "Indore": "Madhya Pradesh", "Kolar": "Karnataka", "Agra": "Uttar Pradesh",
        "Cuttack": "Odisha", "Nasik": "Maharashtra", "Shimla": "Himachal Pradesh"
    }
    
    df['state'] = df['mandi'].map(mandi_state_map).fillna("Other")
    
    state_stats = []
    for state, group in df.groupby('state'):
        if len(group) > 5:
            vol = group['price_modal'].std() / group['price_modal'].mean() if group['price_modal'].mean() > 0 else 0
            avg_price = group['price_modal'].mean()
            state_stats.append({
                "State": state,
                "Volatility": vol,
                "Avg Price": avg_price,
                "Market Count": group['mandi'].nunique()
            })
            
    return pd.DataFrame(state_stats)


def export_prices_to_csv():
    """Export market prices to CSV for Git tracking."""
    try:
        with get_connection() as conn:
            df = pd.read_sql("SELECT * FROM market_prices ORDER BY date", conn)
        
        # Ensure data dir exists
        import os
        if not os.path.exists("data"):
            os.makedirs("data")
            
        df.to_csv("data/market_prices.csv", index=False)
        logger.info("Exported prices to data/market_prices.csv")
    except Exception as e:
        logger.error(f"export_prices_to_csv failed: {e}")


def import_prices_from_csv():
    """Restores prices from CSV and performs incremental sync if new data exists."""
    import os
    import sqlite3
    if not os.path.exists("data/market_prices.csv"):
        logger.warning("Warning: data/market_prices.csv not found.")
        return

    conn = sqlite3.connect(DB_NAME, timeout=30)
    c = conn.cursor()
    
    try:
        # 1. Get current Max Date in DB
        c.execute("SELECT MAX(date) FROM market_prices")
        max_date_db = c.fetchone()[0]
        
        # 2. Load CSV
        df = pd.read_csv("data/market_prices.csv")
        
        if max_date_db:
            # Incremental Sync
            df['date_dt'] = pd.to_datetime(df['date'], errors='coerce')
            max_date_db_dt = pd.to_datetime(max_date_db, errors='coerce')
            
            new_records = df[df['date_dt'] > max_date_db_dt].copy()
            new_records = new_records.drop(columns=['date_dt'])
            
            if not new_records.empty:
                logger.info(f"Syncing {len(new_records)} new records from CSV (Newer than {max_date_db})...")
                # Filter valid columns for market_prices table
                valid_cols = ['date', 'commodity', 'mandi', 'price_min', 'price_max', 'price_modal', 'arrival', 'unit']
                cols_to_save = [col for col in valid_cols if col in new_records.columns]
                new_records[cols_to_save].to_sql('market_prices', conn, if_exists='append', index=False)
                logger.info("Incremental sync successful.")
            else:
                logger.info(f"DB is already up to date (Max Date: {max_date_db}).")
        else:
            # Full Restore (Empty DB)
            logger.info("DB empty. Performing full restoration from CSV...")
            df.to_sql('market_prices', conn, if_exists='append', index=False)
            logger.info(f"Restored {len(df)} records.")
            
        # 3. Finalize Update Metadata — Set last_update to actual max date in DB
        c = conn.cursor()
        c.execute("SELECT MAX(date) FROM market_prices")
        new_max = c.fetchone()[0]
        if new_max:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT OR REPLACE INTO app_metadata (key, value) VALUES ('last_update', ?)", (now_str,))
            logger.info(f"Set last_update to {now_str} (data max: {new_max})")
            
    except Exception as e:
        logger.error(f"CSV Sync failed: {e}", exc_info=True)
    finally:
        conn.commit()
        conn.close()
