
import database.db_manager as db
import pandas as pd
from datetime import datetime

try:
    print("Initializing DB...")
    db.init_db()
    
    print("Testing Log Signal...")
    today = datetime.now().strftime("%Y-%m-%d")
    db.log_signal(today, "Potato", "Agra", "HOLD", 1200)
    
    print("Testing Stats...")
    stats = db.get_signal_stats("Potato", "Agra")
    print(f"Stats: {stats}")
    
    print("DB Verification Success")
except Exception as e:
    print(f"DB Error: {e}")
