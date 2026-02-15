
import sys
import os
import pandas as pd

# Setup path
sys.path.append(os.getcwd())
import database.db_manager as db_manager

def test_warehouse():
    print("--- Testing Data Warehouse Optimizations ---")
    
    # 1. Test Optimization
    print("\nRunning optimize_db()...")
    db_manager.optimize_db()
    
    # 2. Test Aggregation
    print("\nTesting get_state_level_aggregation()...")
    state_df = db_manager.get_state_level_aggregation()
    if not state_df.empty:
        print("✅ State Aggregation Successful:")
        print(state_df.head())
    else:
        print("⚠️ State Aggregation returned empty (might be no data).")
        
    # 3. Test Long Term Trends
    print("\nTesting get_long_term_trends()...")
    # Need a valid commodity/mandi. Let's try One.
    opts = db_manager.get_unique_items('commodity')
    if opts:
        com = opts[0]
        mandis = db_manager.get_unique_items('mandi')
        if mandis:
            man = mandis[0]
            print(f"Fetching for {com}-{man}")
            trend_df = db_manager.get_long_term_trends(com, man)
            if not trend_df.empty:
                print(f"✅ Fetched {len(trend_df)} records.")
            else:
                print("⚠️ No trends found.")
    
if __name__ == "__main__":
    test_warehouse()
