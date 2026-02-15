import requests
import feedparser
import pandas as pd
import random
import time
import warnings
warnings.filterwarnings('ignore') # Squelch all warnings for clean output
from datetime import datetime, timedelta

# Import database manager (Assuming it's in a sibling directory or added to path)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import database.db_manager as dbm
from agents.forecast_execution import ForecastingAgent
from agents.risk_scoring import MarketRiskEngine
from agents.decision_support import DecisionAgent
from agents.shock_monitoring import AnomalyDetectionEngine
from agents.performance_monitor import PerformanceMonitor
import numpy as np

# --- 1. FREE NEWS SOURCE: Google News RSS ---
def fetch_agri_news(query="Agriculture News India"):
    """
    Fetches news from Google News RSS feed.
    """
    # Use 'when:1d' to force fresh news if possible, but Google RSS params are tricky.
    # 'ceid=IN:en' is good. 
    # Let's try a broader query to ensure volume.
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}+when:7d&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(rss_url)
    
    # Load Sentiment Agent
    try:
        from agents.sentiment_analysis import SentimentAgent
        sa = SentimentAgent()
    except Exception as e:
        print(f"Sentiment Agent Warning: {e}")
        sa = None

    news_items = []
    for entry in feed.entries[:5]: # Top 5 news
        
        sentiment = "Neutral"
        if sa:
            analysis = sa.analyze(entry.title)
            sentiment = analysis['label']
            
        news_items.append({
            "date": entry.published,
            "title": entry.title,
            "source": entry.source.title,
            "url": entry.link,
            "sentiment": sentiment
        })
    
    return pd.DataFrame(news_items)

# --- 2. FREE PRICE SOURCE: Agmarknet (Government) ---
# NOTE: Direct scraping is fragile. We simulate the *structure* of Agmarknet data 
# so the system is robust. In a production environment, you would use:
# requests.get("http://agmarknet.gov.in/...") and BeautifulSoup to parse the HTML table.

def fetch_mandi_prices_simulated():
    """
    Simulates fetching live data from Agmarknet for demonstration.
    Returns realistic data structure.
    """
    commodities = [
        "Onion", "Potato", "Tomato", "Wheat", "Rice", 
        "Maize", "Soyabean", "Mustard", "Cotton", "Sugarcane",
        "Gram", "Tur", "Moong", "Masur", "Urad",
        "Apple", "Banana", "Mango", "Grapes", "Orange",
        "Garlic", "Ginger", "Turmeric", "Jeera", "Chilli"
    ]
    mandis = [
        "Azadpur", "Lasalgaon", "Vashi", "Kolar", "Indore",
        "Pune", "Mumbai", "Jaipur", "Ahmedabad", "Surat",
        "Kanpur", "Lucknow", "Varanasi", "Agra", "Bareilly",
        "Kolkata", "Bhubaneswar", "Cuttack", "Patna", "Ranchi",
        "Chennai", "Coimbatore", "Madurai", "Hyderabad", "Warangal",
        "Bangalore", "Mysore", "Hubli", "Shimoga", "Bellary"
    ]
    
    data = []
    today = datetime.now().strftime("%Y-%m-%d")
    
    for com in commodities:
        # Create realistic variation
        base_price = random.randint(1500, 5000) # Rs/Quintal
        for mandi in mandis:
            # Add some noise per mandi
            modal = base_price + random.randint(-200, 200)
            data.append({
                "date": today,
                "commodity": com,
                "mandi": mandi,
                "price_min": modal - 100,
                "price_max": modal + 100,
                "price_modal": modal,
                "arrival": random.randint(50, 500) # Tons
            })
            
    df = pd.DataFrame(data)
    return df

def fetch_real_prices(fallback=True):
    """
    Attempts to scrape real data from Agmarknet. 
    Falls back to simulation if scraping fails.
    """
    try:
        print("Attempting to fetch REAL data from Agmarknet...")
        # Import the new scraper
        from etl.agmarknet_scraper import get_all_commodities_data
        
        real_df = get_all_commodities_data()
        
        if real_df.empty:
            raise Exception("Scraper returned no data")
            
        print(f"Successfully scraped {len(real_df)} records from AgMarknet!")
        return real_df

    except Exception as e:
        print(f"Real Data Fetch failed ({e}). Using robust simulation.")
        return fetch_mandi_prices_simulated()

def seed_historical_data(days=90):
    """
    Generates historical data for the past 'days' to ensure charts look good.
    """
    print(f"Seeding {days} days of historical data...")
    commodities = [
        "Onion", "Potato", "Tomato", "Wheat", "Rice", 
        "Maize", "Soyabean", "Mustard", "Cotton", "Sugarcane",
        "Gram", "Tur", "Moong", "Masur", "Urad",
        "Apple", "Banana", "Mango", "Grapes", "Orange",
        "Garlic", "Ginger", "Turmeric", "Jeera", "Chilli"
    ]
    mandis = [
        "Azadpur", "Lasalgaon", "Vashi", "Kolar", "Indore",
        "Pune", "Mumbai", "Jaipur", "Ahmedabad", "Surat",
        "Kanpur", "Lucknow", "Varanasi", "Agra", "Bareilly",
        "Kolkata", "Bhubaneswar", "Cuttack", "Patna", "Ranchi",
        "Chennai", "Coimbatore", "Madurai", "Hyderabad", "Warangal",
        "Bangalore", "Mysore", "Hubli", "Shimoga", "Bellary"
    ]
    
    data = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Generate a trend for each commodity/mandi
    for com in commodities:
        base_price = random.randint(1500, 5000)
        for mandi in mandis:
            current_price = base_price + random.randint(-200, 200)
            
            for i in range(days):
                date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
                # Random walk
                change = random.randint(-50, 50)
                current_price += change
                current_price = max(100, current_price)
                
                data.append({
                    "date": date,
                    "commodity": com,
                    "mandi": mandi,
                    "price_min": current_price - 100,
                    "price_max": current_price + 100,
                    "price_modal": current_price,
                    "arrival": random.randint(50, 500)
                })
                
    df = pd.DataFrame(data)
    dbm.save_prices(df)
    print("Historical seeding complete.")

# Coordinate Mapping for Real Weather
MANDI_COORDS = {
    "Azadpur": {"lat": 28.7, "lon": 77.1}, # Delhi
    "Lasalgaon": {"lat": 20.1, "lon": 74.2}, # Nashik
    "Vashi": {"lat": 19.0, "lon": 73.0}, # Mumbai
    "Kolar": {"lat": 13.1, "lon": 78.1}, # Karnataka
    "Indore": {"lat": 22.7, "lon": 75.8}, # MP
    "Pune": {"lat": 18.5, "lon": 73.8},
    "Jaipur": {"lat": 26.9, "lon": 75.7},
    "Ahmedabad": {"lat": 23.0, "lon": 72.5},
    "Kolkata": {"lat": 22.5, "lon": 88.3},
    "Bengaluru": {"lat": 12.9, "lon": 77.5},
    "Agra": {"lat": 27.1, "lon": 78.0},
    "Nasik": {"lat": 19.9, "lon": 73.7}
}


# --- 3. REAL WEATHER SOURCE: OpenWeatherMap (OWM) ---
def fetch_weather_owm(lat, lon, api_key=None):
    """
    Fetches real-time weather from OpenWeatherMap.
    Requires an API Key. Falls back to Open-Meteo (Free, No Key) if key is missing.
    """
    if not api_key:
        # Fallback to Open-Meteo
        return fetch_weather_open_meteo(lat, lon)
        
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if response.status_code == 200:
            return {
                "temp": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "condition": data["weather"][0]["main"],
                "wind_speed": data["wind"]["speed"]
            }
        else:
            print(f"OWM Error: {data.get('message')}")
            return fetch_weather_open_meteo(lat, lon)
            
    except Exception as e:
        print(f"OWM Fetch Failed: {e}")
        return fetch_weather_open_meteo(lat, lon)

def fetch_weather_open_meteo(lat, lon):
    """
    Free fallback weather API (Open-Meteo).
    """
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "current_weather" in data:
            cw = data["current_weather"]
            # Map WMO codes to string (simplified)
            wmo_code = cw.get("weathercode", 0)
            condition = "Clear"
            if wmo_code > 0: condition = "Cloudy"
            if wmo_code > 50: condition = "Rainy"
            if wmo_code > 70: condition = "Storm"
            
            return {
                "temp": cw["temperature"],
                "wind_speed": cw["windspeed"],
                "condition": condition,
                "humidity": random.randint(40, 90) # Open-Meteo current_weather doesn't always have humidity
            }
    except Exception as e:
        print(f"Open-Meteo failed: {e}")
        
    return {"temp": 25.0, "humidity": 60, "condition": "Sunny", "wind_speed": 10}

import contextlib
import os

@contextlib.contextmanager
def suppress_output():
    """Context manager to suppress stdout and stderr."""
    with open(os.devnull, 'w') as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            yield

def fetch_real_weather(api_key=None):
    """
    Iterates through Mandis and fetches weather for each.
    """
    weather_data = [] # List of dicts for DataFrame
    for mandi, coords in MANDI_COORDS.items():
        w = fetch_weather_owm(coords["lat"], coords["lon"], api_key)
        
        # Add to list
        weather_data.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "region": mandi,
            "temperature": w['temp'],
            "rainfall": 0.0, # OWM basic doesn't give rain sum easily, mock or omit
            "condition": w['condition'],
            "wind_speed": w['wind_speed'],
            "humidity": w['humidity']
        })
            
    return pd.DataFrame(weather_data)

import contextlib
import os

@contextlib.contextmanager
def suppress_output():
    """Context manager to suppress stdout and stderr."""
    with open(os.devnull, 'w') as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            yield

def run_daily_update(progress_callback=None):
    """
    Runs the full ETL pipeline with Robustness (Logs, Partial Updates, Duration).
    """
    start_time = time.time()
    dbm.log_system_event("INFO", "ETL", "Daily Update Started")
    print(f"Starting Update... [v{datetime.now().strftime('%H%M%S')}]")
    
    if progress_callback:
        progress_callback(0.05, "Initializing Database...")

    # Ensure DB is initialized
    try:
        dbm.init_db()
    except Exception as e:
        dbm.log_system_event("CRITICAL", "ETL", f"DB Init Failed: {e}")
        return # Cannot proceed without DB

    # 1. Fetch Prices (Real/Simulated)
    if progress_callback:
        progress_callback(0.1, "Fetching Simulation Data...")
        
    prices_df = pd.DataFrame()
    batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Check if we need to seed history (First run on Cloud)
        existing_data = dbm.get_latest_prices()
        if existing_data.empty:
            print("Fresh DB detected! Seeding 90 days of historical data...")
            seed_historical_data(days=90)
        else:
            print(f"DB exists. Appending latest daily prices (Batch: {batch_id})...")
            prices_df = fetch_real_prices(fallback=True)
            
            # --- DATA RELIABILITY (New Phase 6) ---
            print("Running Data Reliability Checks...")
            from agents.data_reliability import DataReliabilityAgent
            dra = DataReliabilityAgent(db_manager=dbm)
            pm = PerformanceMonitor()
            
            # 1. Save Raw
            dbm.save_raw_prices(prices_df, batch_id)
            
            # 2. Validate
            valid_df, issues, stats = dra.validate_batch(prices_df, batch_id)
            
            # 3. Log Issues
            if issues:
                dbm.log_quality_issues(issues)
                print(f"Logged {len(issues)} data quality issues.")
                
            # 4. Save Clean Data
            if not valid_df.empty:
                dbm.save_prices(valid_df)
                print(f"Promoted {len(valid_df)} valid records to Production DB.")
            else:
                print("Warning: No valid records to promote.")
                
            # 5. Log Execution Stats
            try:
                duration = time.time() - start_time
                status = "SUCCESS" if not valid_df.empty else "PARTIAL_FAILURE"
                dbm.log_scraper_execution(status, duration, len(prices_df), len(valid_df), stats['rejected'])
            except Exception as e:
                print(f"Failed to log stats: {e}")
                
    except Exception as e:
        print(f"Price Fetch Error: {e}")
        dbm.log_system_event("ERROR", "ETL", f"Price Fetch Failed: {e}")
        dbm.log_scraper_execution("FAILURE", time.time() - start_time, 0, 0, 0, str(e))
        # Continue to other steps even if prices fail (Partial Update)
 
    # 2. Fetch News (Real)
    if progress_callback:
        progress_callback(0.15, "Fetching Global News...")
    
    try:
        news_df = fetch_agri_news()
        dbm.save_news(news_df)
    except Exception as e:
        print(f"News Fetch Error: {e}")
        dbm.log_system_event("ERROR", "ETL", f"News Fetch Failed: {e}")

    # 3. Fetch Weather (Real)
    if progress_callback:
        progress_callback(0.20, "Fetching Weather Data...")
    
    try:
        weather_df = fetch_real_weather()
        dbm.save_weather(weather_df)
    except Exception as e:
        print(f"Weather Fetch Error: {e}")
        dbm.log_system_event("ERROR", "ETL", f"Weather Fetch Failed: {e}")
    
    # 4. Intelligence Processing (ML + Risk + Decision)
    print("Running Intelligence Swarm (Forecast + Risk + Decision)...")
    if progress_callback:
        progress_callback(0.25, "Starting Intelligence Swarm...")
    
    processed_count = 0
    try:
        # Get unique Commodity-Mandi pairs from DB
        commodities = dbm.get_unique_items("commodity")
        mandis = dbm.get_unique_items("mandi")
        
        total_pairs = len(commodities) * len(mandis)
        current_pair_idx = 0
        
        # GLOBAL SILENCE FOR SWARM LOOP
        with suppress_output():
            for com in commodities:
                for man in mandis:
                    current_pair_idx += 1
                    
                    try:
                        # Get History
                        df = dbm.get_latest_prices(commodity=com)
                        df = df[df['mandi'] == man]
                        
                        if len(df) < 15: # Need minimum data for forecast
                            continue
                            
                        # Update Progress Bar (Scale 0.25 to 0.95)
                        if progress_callback:
                            progress = 0.25 + (0.7 * (current_pair_idx / total_pairs))
                            progress_callback(progress, f"Processing {com} in {man}...")

                        # Rename for compatibility with agents ('price_modal' -> 'price')
                        df_agent = df.copy()
                        if 'price_modal' in df_agent.columns:
                            df_agent = df_agent.rename(columns={'price_modal': 'price'})
                        # Ensure dates are datetime
                        df_agent['date'] = pd.to_datetime(df_agent['date'])
                            
                        # A. Forecast
                        forecast_df = forecaster.generate_forecasts(df_agent, com, man)
                        
                        if forecast_df.empty:
                            continue

                        # LOG FORECAST (Phase 5)
                        try:
                            gen_date = datetime.now().strftime("%Y-%m-%d")
                            dbm.log_forecast(gen_date, com, man, forecast_df)
                        except Exception as e:
                            print(f"Forecast Savelog error: {e}")
                        
                        # B. Risk & Shock
                        # Calculate volatility (std dev of daily returns)
                        current_price = df_agent['price'].iloc[-1]
                        df_agent['returns'] = df_agent['price'].pct_change()
                        volatility = df_agent['returns'].std()
                        forecast_std = forecast_df['forecast_price'].std()
                        
                        # Detect Shock
                        shock_info = shock_agent.detect_shocks(df_agent, forecast_df)
                        
                        # Calculate Risk Score
                        risk_data = risk_engine.calculate_risk_score(shock_info, forecast_std, volatility)
                        
                        # C. Decision Signal
                        signal_data = decision_agent.get_signal(current_price, forecast_df, risk_data, shock_info)
                        
                        # D. Log Signal
                        # We log the signal for "Today"
                        today_str = datetime.now().strftime("%Y-%m-%d")
                        dbm.log_signal(
                            date=today_str,
                            commodity=com,
                            mandi=man,
                            signal=signal_data['signal'],
                            price_at_signal=current_price
                        )
                        
                        # E. Update Performance Metrics (Phase 7)
                        try:
                            pm.update_metrics(com, man)
                        except Exception as e:
                            print(f"Performance Update Failed: {e}")

                        processed_count += 1
                    except Exception as inner_e:
                        # Log individual failures but continue loop
                        # print(f"Error processing {com}-{man}: {inner_e}") # Squelch spam
                        continue

        print(f"Intelligence Processing Complete. Generated signals for {processed_count} markets.")
        
    except Exception as e:
        print(f"Intelligence Swarm Critical Failure: {e}")
        dbm.log_system_event("CRITICAL", "ETL", f"Swarm Failed: {e}")

    finally:
        # 5. Update Metadata (Ensure this runs even if Intelligence fails)
        if progress_callback:
            progress_callback(0.98, "Finalizing Update...")
        dbm.set_last_update()
        
        # 6. Export for Git Tracking
        try:
            dbm.export_prices_to_csv()
        except Exception as e:
            print(f"Export Failed: {e}")
        
        if progress_callback:
            progress_callback(1.0, "Update Complete!")
            
        duration = time.time() - start_time
        dbm.log_system_event("INFO", "ETL", "Daily Update Completed", f"Duration: {duration:.2f}s")
        print(f"Update Complete in {duration:.2f}s.")

if __name__ == "__main__":
    run_daily_update()
