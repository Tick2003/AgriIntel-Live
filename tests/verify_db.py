import sqlite3
import pandas as pd

conn = sqlite3.connect('agri_intel.db')
try:
    df = pd.read_sql("SELECT * FROM voice_call_logs", conn)
    print(f"Total Logs Captured: {len(df)}")
    if not df.empty:
        print("\n--- Last 5 Interactions ---")
        print(df[['phone_number', 'timestamp', 'language', 'intent', 'transcript', 'response_text']].tail(5))
except Exception as e:
    print(f"Verification failed: {e}")
finally:
    conn.close()
