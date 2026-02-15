
import sqlite3
import os
import sys

# Setup
sys.path.append(os.getcwd())

def cleanup():
    print("Cleaning up test data...")
    conn = sqlite3.connect("agri_intel.db")
    com = "TestCropPerf"
    try:
        conn.execute(f"DELETE FROM market_prices WHERE commodity='{com}'")
        conn.execute(f"DELETE FROM forecast_logs WHERE commodity='{com}'")
        conn.execute(f"DELETE FROM model_metrics WHERE commodity='{com}'")
        conn.commit()
        print("Cleanup successful.")
    except Exception as e:
        print(f"Cleanup failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup()
