import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Ensure root is in path to import database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.db_manager import get_latest_prices, get_latest_news, get_weather_logs

def load_css():
    """
    Returns custom CSS for the dashboard.
    """
    return """
    <style>
        .stApp {
            background-color: #f8f9fa;
        }
        .metric-card {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
    </style>
    """

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
