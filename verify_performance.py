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
    com = "TestCrop"
    man = "TestMandi"
    gen_date = "2023-01-01"
    
    # Create Dummy Forecast DF
    dates = pd.date_range(start="2023-01-02", periods=5)
    forecast_df = pd.DataFrame({
        "date": dates,
        "forecast_price": [100, 105, 110, 108, 112]
    })
    
    # Inject Forecasts
    log_forecast(gen_date, com, man, forecast_df)
    
    # Inject Actuals (overwrite market_prices for test)
    conn = sqlite3.connect("agri_intel.db")
    # Clean previous test data
    conn.execute(f"DELETE FROM market_prices WHERE commodity='{com}'")
    conn.execute(f"DELETE FROM forecast_logs WHERE commodity='{com}'")
    
    # Re-Log Forecast (since we deleted)
    log_forecast(gen_date, com, man, forecast_df)
    
    # Log Matches
    actual_prices = [102, 104, 115, 100, 110] # Some error
    for d, p in zip(dates, actual_prices):
        conn.execute("INSERT INTO market_prices (date, commodity, mandi, price_modal) VALUES (?, ?, ?, ?)", 
                     (d.strftime("%Y-%m-%d"), com, man, p))
    conn.commit()
    conn.close()
    
    # 3. Test Performance Monitor Calculation
    pm = PerformanceMonitor()
    metrics = pm.calculate_metrics(com, man)
    
    print(f"Calculated Metrics: {metrics}")
    
    if metrics['n'] == 5:
        print("✅ Sample Size Correct")
    else:
        print(f"❌ Sample Size Mismatch: Expected 5, got {metrics['n']}")
        
    # Check MAPE logic
    # Errors: |100-102|=2, |105-104|=1, |110-115|=5, |108-100|=8, |112-110|=2
    # Pct: 2/102, 1/104, 5/115, 8/100, 2/110
    # Approx: 0.019, 0.009, 0.043, 0.08, 0.018
    # Mean: ~0.033 -> 3.3%
    
    if 2.0 < metrics['mape'] < 5.0:
        print(f"✅ MAPE is reasonable ({metrics['mape']}%)")
    else:
        print(f"❌ MAPE Value unexpected: {metrics['mape']}%")
        
    # 4. Test Backtest
    # We need enough history for backtest. The mock above is small.
    # We'll just check if the function 'runs' and returns insufficient data safely.
    print("Testing Backtest (Safety Check)...")
    res = pm.run_backtest(com, man) # Should likely fail due to insufficient history
    print(f"Backtest Result: {res['status']}")
    
    if res['status'] == 'Failed':
        print("✅ Backtest handled insufficient data correctly.")
    else:
        print("⚠️ Backtest ran unexpectedly (might have found other data).")

if __name__ == "__main__":
    test_performance_tracking()
