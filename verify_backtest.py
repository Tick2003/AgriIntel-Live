
import pandas as pd
import sqlite3
import os
import sys

# Setup
sys.path.append(os.getcwd())
from database.db_manager import init_db
from agents.backtesting_engine import BacktestEngine

def test_backtesting():
    print("--- Testing Backtesting Engine ---")
    
    # 1. Setup DB with mock data
    init_db()
    conn = sqlite3.connect("agri_intel.db")
    com = "TestCropBT"
    man = "TestMandiBT"
    
    # Check if data exists, if not inject
    print("Injecting Mock Price History...")
    dates = pd.date_range(start="2023-01-01", periods=100)
    import numpy as np
    
    # Generate a sine wave price to force MA crossovers
    x = np.linspace(0, 4*np.pi, 100)
    prices = 100 + 10 * np.sin(x) # Oscillates between 90 and 110
    
    conn.execute(f"DELETE FROM market_prices WHERE commodity='{com}'")
    
    for d, p in zip(dates, prices):
        conn.execute("INSERT INTO market_prices (date, commodity, mandi, price_modal) VALUES (?, ?, ?, ?)", 
                     (d.strftime("%Y-%m-%d"), com, man, p))
    conn.commit()
    conn.close()
    
    # 2. Run Backtest
    be = BacktestEngine(initial_capital=10000)
    print("Running simulation...")
    equity_df, metrics, trades_df = be.run_backtest(com, man)
    
    # 3. Verify Results
    if metrics is None:
        print("❌ Backtest returned None.")
        return
        
    print("Metrics:", metrics)
    
    if metrics['Trade Count'] > 0:
        print(f"✅ Trades Executed: {metrics['Trade Count']}")
    else:
        print("⚠️ No trades executed (Check logic or data).")
        
    if not equity_df.empty:
        print(f"✅ Equity Curve Generated: {len(equity_df)} days")
    else:
        print("❌ Equity Curve Empty")

    # Check for basic sanity
    if metrics['Final Equity'] != 10000:
        print(f"✅ P&L Changed: {metrics['Final Equity']}")
    else:
        print("⚠️ Equity did not change (No trades?).")

    # Cleanup
    conn = sqlite3.connect("agri_intel.db")
    conn.execute(f"DELETE FROM market_prices WHERE commodity='{com}'")
    conn.commit()
    conn.close()
    print("Cleanup Complete.")

if __name__ == "__main__":
    test_backtesting()
