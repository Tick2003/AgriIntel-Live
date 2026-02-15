
import sys
import os
import importlib

# Add project root to path
sys.path.append(os.getcwd())

print("Checking database exports...")
try:
    import database
    if hasattr(database, 'save_raw_prices'):
        print("PASS: database exports save_raw_prices")
    else:
        print("FAIL: database MISSING save_raw_prices")

    if hasattr(database, 'log_scraper_execution'):
        print("PASS: database exports log_scraper_execution")
    else:
        print("FAIL: database MISSING log_scraper_execution")
except Exception as e:
    print(f"FAIL: Error importing database: {e}")

print("\nChecking reload logic...")
try:
    import database.db_manager as db_manager
    import etl.data_loader
    
    importlib.reload(db_manager)
    print("PASS: db_manager reloaded")
    
    importlib.reload(etl.data_loader)
    print("PASS: etl.data_loader reloaded")
    
except Exception as e:
    print(f"FAIL: Reload error: {e}")
