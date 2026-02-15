
import sys
import os
sys.path.append(os.getcwd())

import etl.data_loader as dl
import database.db_manager as dbm
import pandas as pd

def test_news():
    print("Testing News Fetching...")
    try:
        news_df = dl.fetch_agri_news()
        print(f"Fetched {len(news_df)} items.")
        if not news_df.empty:
            print("First item:", news_df.iloc[0].to_dict())
            
            # Test Saving
            print("Testing DB Save...")
            dbm.save_news(news_df)
            print("Saved to DB.")
            
            # Verify Save
            print("Verifying in DB...")
            import sqlite3
            conn = sqlite3.connect("agri_intel.db")
            # Ordering by date instead of id
            saved = pd.read_sql("SELECT * FROM news_alerts ORDER BY date DESC LIMIT 5", conn)
            print("Latest 5 DB items:")
            print(saved) 
            conn.close()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_news()
