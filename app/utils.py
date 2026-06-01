# AgriIntel.in Utils
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import streamlit as st

# Ensure root is in path to import database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3
from database.db_manager import get_latest_prices, get_latest_news, get_weather_logs

def get_db_options():
    """Fetch all unique commodities and mandis directly."""
    try:
        # Locate DB file robustly
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "agri_intel.db")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get Commodities
        cursor.execute("SELECT DISTINCT commodity FROM market_prices ORDER BY commodity")
        commodities = [row[0] for row in cursor.fetchall()]
        
        # Get Mandis
        cursor.execute("SELECT DISTINCT mandi FROM market_prices ORDER BY mandi")
        mandis = [row[0] for row in cursor.fetchall()]
        
        conn.close()

        # Fallback if empty (e.g. fresh install)
        if not commodities: commodities = ["Potato", "Onion", "Tomato"]
        if not mandis: mandis = ["Agra", "Nasik", "Bengaluru"]
        return commodities, mandis
    except Exception as e:
        print(f"Error fetching DB options: {e}")
        return ["Potato", "Onion", "Tomato"], ["Agra", "Nasik", "Bengaluru"]


def get_live_data(commodity: str = "Potato", mandi: str = "Agra") -> pd.DataFrame:
    """
    Fetches LIVE data from the collected database.
    """
    try:
        df = get_latest_prices(commodity)
        
        # Filter by mandi if provided (The mocked data might just check commodity)
        if not df.empty and mandi:
            # Simple filter, assuming exact match or partial
            df = df[df['mandi'] == mandi]
        
        if df.empty:
            # Fallback if no data found for specific selection
            st.warning(f"No live data found for {commodity} in {mandi}. Showing dummy data.")
            return get_dummy_data_fallback(commodity, mandi)
            
        # Standardize columns for the app
        # DB has: date, commodity, mandi, price_min, price_max, price_modal, arrival
        # App expects: date, price, arrival, commodity, mandi
        df = df.rename(columns={'price_modal': 'price'})
        
        # Ensure date is datetime
        df['date'] = pd.to_datetime(df['date'])
        
        return df.sort_values('date')
        
    except Exception as e:
        print(f"DB Error: {e}")
        return get_dummy_data_fallback(commodity, mandi)

def get_dummy_data_fallback(commodity, mandi):
    """
    Legacy dummy generator for fallback.
    """
    dates = pd.date_range(end=datetime.today(), periods=90)
    base_price = 1500 if commodity == "Potato" else 3000
    prices = [base_price]
    for _ in range(89):
        prices.append(prices[-1] + np.random.normal(0, base_price * 0.05))
    
    return pd.DataFrame({
        "date": dates,
        "price": prices,
        "arrival": np.random.randint(100, 1000, size=90),
        "commodity": commodity,
        "mandi": mandi
    })

def get_news_feed():
    """Fetch structured news."""
    try:
        return get_latest_news()
    except:
        return pd.DataFrame()

def get_weather_data():
    """Fetch weather logs."""
    try:
        return get_weather_logs()
    except:
        return pd.DataFrame()


# --- REAL-TIME UTILITIES ---

def get_intraday_data(commodity: str, mandi: str, limit: int = 50) -> pd.DataFrame:
    """Fetch latest intraday trades from the database."""
    try:
        from database.db_manager import get_latest_intraday_trades
        df = get_latest_intraday_trades(commodity, mandi, limit)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        print(f"Intraday data error: {e}")
        return pd.DataFrame()


def get_order_book_data(commodity: str, mandi: str, depth: int = 10) -> dict:
    """Build a live order book from recent BID/ASK entries."""
    try:
        from etl.realtime_stream import get_order_book
        return get_order_book(commodity, mandi, depth)
    except Exception as e:
        print(f"Order book error: {e}")
        return {"bids": pd.DataFrame(), "asks": pd.DataFrame()}


def get_intraday_price_series(commodity: str, mandi: str, limit: int = 100) -> pd.DataFrame:
    """Get executed trade prices for intraday charting."""
    try:
        from database.db_manager import get_latest_intraday_trades
        df = get_latest_intraday_trades(commodity, mandi, limit * 3)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            # Filter to executed trades only for price chart
            trades = df[df['trade_type'] == 'TRADE'].head(limit)
            if trades.empty:
                # Use all ticks if no TRADE type
                trades = df.head(limit)
            return trades.sort_values('timestamp')
        return pd.DataFrame()
    except Exception as e:
        print(f"Intraday price series error: {e}")
        return pd.DataFrame()
