
import sqlite3
import pandas as pd

try:
    conn = sqlite3.connect('agri_intel.db')
    
    # List tables
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
    print("Tables:", tables)
    
    if 'market_prices' in tables['name'].values:
        # Get sample data
        df = pd.read_sql("SELECT * FROM market_prices ORDER BY date DESC LIMIT 20", conn)
        print("\nColumns:", df.columns.tolist())
        print("\nLatest 20 records:")
        print(df)
        
        # Check specific counts
        count = pd.read_sql("SELECT commodity, mandi, COUNT(*) as cnt FROM market_prices GROUP BY commodity, mandi", conn)
        print("\nCounts per commodity/mandi:")
        print(count)
    else:
        print("market_prices table not found!")

except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
