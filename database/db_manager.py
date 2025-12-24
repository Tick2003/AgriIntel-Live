import sqlite3
import pandas as pd
from datetime import datetime, timedelta

DB_NAME = "agri_intel.db"

def init_db():
    """Initialize the database with necessary tables."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Table: Market Prices
    c.execute('''
        CREATE TABLE IF NOT EXISTS market_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            commodity TEXT,
            mandi TEXT,
            price_min REAL,
            price_max REAL,
            price_modal REAL,
            arrival REAL,
            unit TEXT DEFAULT 'Rs/Quintal'
        )
    ''')
    
    # Table: News/Alerts
    c.execute('''
        CREATE TABLE IF NOT EXISTS news_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            title TEXT,
            source TEXT,
            url TEXT,
            sentiment TEXT
        )
    ''')

    # Table: Weather Logs
    c.execute('''
        CREATE TABLE IF NOT EXISTS weather_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            region TEXT,
            temperature REAL,
            rainfall REAL,
            condition TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Database {DB_NAME} initialized.")

def save_prices(df):
    """Save a pandas DataFrame of prices to the DB."""
    conn = sqlite3.connect(DB_NAME)
    # Ensure columns match
    # Expected DF cols: ['date', 'commodity', 'mandi', 'price_min', 'price_max', 'price_modal', 'arrival']
    df.to_sql('market_prices', conn, if_exists='append', index=False)
    conn.close()
    print(f"Saved {len(df)} price records.")

def get_latest_prices(commodity=None):
    """Retrieve prices from the DB."""
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT * FROM market_prices"
    if commodity:
        query += f" WHERE commodity = '{commodity}'"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

if __name__ == "__main__":
    init_db()
