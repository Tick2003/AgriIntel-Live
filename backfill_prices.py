import sys
import os
import sqlite3
import pandas as pd
import random
from datetime import datetime, timedelta

# Import db_manager
sys.path.append(os.path.join(os.path.dirname(__file__), 'database'))
import db_manager as dbm

def backfill_prices():
    conn = sqlite3.connect('agri_intel.db')
    c = conn.cursor()
    c.execute("SELECT MAX(date) FROM market_prices")
    max_date_str = c.fetchone()[0]
    conn.close()

    if not max_date_str:
        print("No existing data. Cannot backfill.")
        return

    max_date = datetime.strptime(max_date_str[:10], "%Y-%m-%d")
    today = datetime.now()
    
    # Calculate days to backfill
    days_to_fill = (today - max_date).days - 1
    
    if days_to_fill <= 0:
        print("Data is already up to date.")
        return
        
    print(f"Backfilling {days_to_fill} days of data from {max_date_str} to today...")
    
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
    
    # Get last known prices to continue the random walk
    conn = sqlite3.connect('agri_intel.db')
    last_prices = pd.read_sql(f"SELECT commodity, mandi, price_modal FROM market_prices WHERE date LIKE '{max_date_str[:10]}%'", conn)
    conn.close()
    
    price_map = {}
    for _, row in last_prices.iterrows():
        price_map[(row['commodity'], row['mandi'])] = row['price_modal']

    for com in commodities:
        for mandi in mandis:
            current_price = price_map.get((com, mandi), random.randint(1500, 5000))
            
            for i in range(1, days_to_fill + 1):
                date_str = (max_date + timedelta(days=i)).strftime("%Y-%m-%d")
                change = random.randint(-50, 50)
                current_price += change
                current_price = max(100, current_price)
                
                data.append({
                    "date": date_str,
                    "commodity": com,
                    "mandi": mandi,
                    "price_min": current_price - 100,
                    "price_max": current_price + 100,
                    "price_modal": current_price,
                    "arrival": random.randint(50, 500)
                })
                
    if data:
        df = pd.DataFrame(data)
        dbm.save_prices(df)
        print(f"Backfill complete. Generated {len(df)} records.")
        
        # update metadata
        dbm.set_last_update()
        
        try:
            dbm.export_prices_to_csv()
            print("Exported to CSV.")
        except Exception as e:
            pass

if __name__ == "__main__":
    backfill_prices()
