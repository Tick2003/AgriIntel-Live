
import pandas as pd
import sqlite3
import os
import sys

# Setup
sys.path.append(os.getcwd())
from database.db_manager import init_db, log_forecast, get_forecast_vs_actuals, log_model_metrics
from agents.performance_monitor import PerformanceMonitor

def test_performance_tracking():
    print("--- Testing Performance Tracking Module ---")
    
    # 1. Ensure DB and Tables exist
    init_db()
    
    # 2. Mock Data Injection
    print("Injecting Mock Forecast Logs...")
    com = "TestCropPerf"
    man = "TestMandiPerf"
    gen_date = "2023-01-01"
    
    # Create Dummy Forecast DF
    dates = pd.date_range(start="2023-01-02", periods=5)
    # Convert to string YYYY-MM-DD to ensure matching
    date_strs = [d.strftime("%Y-%m-%d") for d in dates]
    
    forecast_df = pd.DataFrame({
        "date": date_strs,
        "forecast_price": [100, 105, 110, 108, 112]
    })
    
    # Inject Forecasts
    log_forecast(gen_date, com, man, forecast_df)
    
    # Inject Actuals (overwrite market_prices for test)
    conn = sqlite3.connect("agri_intel.db")
    # Clean previous test data
    conn.execute(f"DELETE FROM market_prices WHERE commodity='{com}'")
    conn.execute(f"DELETE FROM forecast_logs WHERE commodity='{com}'")
    conn.execute(f"DELETE FROM model_metrics WHERE commodity='{com}'")
        
    # Re-Log Forecast (since we deleted)
    log_forecast(gen_date, com, man, forecast_df)
    
    # Log Matches
    actual_prices = [102, 104, 115, 100, 110] # Some error
    for d, p in zip(dates, actual_prices):
        conn.execute("INSERT INTO market_prices (date, commodity, mandi, price_modal) VALUES (?, ?, ?, ?)", 
                     (d.strftime("%Y-%m-%d"), com, man, p))
    conn.commit()
    
    # DEBUG: Dump Tables
    print("DEBUG: forecast_logs content:")
    try:
        print(pd.read_sql(f"SELECT * FROM forecast_logs WHERE commodity='{com}'", conn))
    except Exception as e:
        print(f"Error reading forecast_logs: {e}")
        
    print("DEBUG: market_prices content:")
    try:
        print(pd.read_sql(f"SELECT * FROM market_prices WHERE commodity='{com}'", conn))
    except Exception as e:
        print(f"Error reading market_prices: {e}")

    conn.close()
    
    # 3. Test Performance Monitor Calculation
    pm = PerformanceMonitor()
    print("Running update_metrics...")
    metrics = pm.update_metrics(com, man)
    
    print(f"Calculated Metrics: {metrics}")
    
    if metrics and metrics['n'] == 5:
        print("✅ Sample Size Correct")
    else:
        print(f"❌ Sample Size Mismatch: Expected 5, got {metrics.get('n') if metrics else 'None'}")
        
    # Check MAE and Health Score
    if metrics:
        if 3.0 < metrics['mae'] < 4.0:
            print(f"✅ MAE is correct ({metrics['mae']})")
        else:
            print(f"❌ MAE Value unexpected: {metrics['mae']}")

        if metrics['health_score'] > 90:
            print(f"✅ Health Score is reasonable ({metrics['health_score']})")
        else:
            print(f"❌ Health Score unexpected: {metrics['health_score']}")

    # 4. Verify DB Storage
    conn = sqlite3.connect("agri_intel.db")
    c = conn.cursor()
    c.execute(f"SELECT mae, health_score FROM model_metrics WHERE commodity='{com}' ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    
    if row:
        print(f"✅ DB Log Verified: MAE={row[0]}, Health={row[1]}")
    else:
        print("❌ DB Log Failed: No record found.")

    # Cleanup
    print("Cleaning up test data...")
    conn = sqlite3.connect("agri_intel.db")
    conn.execute(f"DELETE FROM market_prices WHERE commodity='{com}'")
    conn.execute(f"DELETE FROM forecast_logs WHERE commodity='{com}'")
    conn.execute(f"DELETE FROM model_metrics WHERE commodity='{com}'")
    conn.commit()
    conn.close()
    print("Cleanup Complete.")

if __name__ == "__main__":
    test_performance_tracking()
