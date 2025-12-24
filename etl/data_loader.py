import requests
import feedparser
import pandas as pd
import random
from datetime import datetime, timedelta

# Import database manager (Assuming it's in a sibling directory or added to path)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.db_manager import save_prices

# --- 1. FREE NEWS SOURCE: Google News RSS ---
def fetch_agri_news(query="Agriculture Market India"):
    """
    Fetches news from Google News RSS feed.
    """
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(rss_url)
    
    news_items = []
    for entry in feed.entries[:5]: # Top 5 news
        news_items.append({
            "date": entry.published,
            "title": entry.title,
            "source": entry.source.title,
            "url": entry.link
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
    commodities = ["Onion", "Potato", "Tomato", "Wheat", "Rice"]
    mandis = ["Azadpur", "Lasalgaon", "Vashi", "Kolar", "Indore"]
    
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

def seed_historical_data(days=90):
    """
    Generates historical data for the past 'days' to ensure charts look good.
    """
    print(f"Seeding {days} days of historical data...")
    commodities = ["Onion", "Potato", "Tomato", "Wheat", "Rice"]
    mandis = ["Azadpur", "Lasalgaon", "Vashi", "Kolar", "Indore"]
    
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
    save_prices(df)
    print("Historical seeding complete.")

def run_daily_update():
    """
    Master function to run the daily update.
    """
    print("Starting Update...")
    
    # Check if DB is empty (naive check) or just seed if needed
    # For demo, we just add today's data. 
    # BUT, if we want to ensure history, we might run seed if called explicitly.
    # For this execution, I'll call seed_historical_data() once manually or here.
    
    # Let's check if we should seed (e.g. if file is small or based on arg)
    # We will just fetch today's simulated data normally.
    # Use 'seed' arg to force history.
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'seed':
        seed_historical_data()
        return

    # 1. Fetch Prices (Today)
    prices_df = fetch_mandi_prices_simulated()
    save_prices(prices_df)

    
    # 2. Fetch News (Real)
    news_df = fetch_agri_news()
    print("Latest News:")
    print(news_df[['title', 'source']].head())
    
    print("Update Complete.")

if __name__ == "__main__":
    run_daily_update()
