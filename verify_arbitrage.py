
import sys
import os
import pandas as pd
from datetime import datetime

# Setup path
sys.path.append(os.getcwd())
from agents.arbitrage_engine import ArbitrageAgent

def test_arbitrage():
    agent = ArbitrageAgent()
    
    # Mock Data
    data = [
        {"mandi": "Azadpur", "commodity": "Onion", "price": 1500, "date": "2026-02-15"},
        {"mandi": "Pune", "commodity": "Onion", "price": 2500, "date": "2026-02-15"}, # Profitable target
        {"mandi": "Kolar", "commodity": "Onion", "price": 1600, "date": "2026-02-15"}  # Unprofitable
    ]
    df = pd.DataFrame(data)
    
    # Config
    cost_cfg = {
        "fuel_rate": 0.02, # 20 INR/km/ton = 0.02 INR/km/Qt
        "toll": 500,
        "labor": 100,
        "spoilage": 0.05
    }
    
    print("--- Running Arbitrage Scan (From Azadpur) ---")
    res = agent.find_opportunities("Onion", "Azadpur", df, {"is_shock": False}, cost_cfg)
    
    if not res.empty:
        print(res[['Target Mandi', 'Net Profit/Qt', 'Profit (Bear Case)', 'Confidence']])
    else:
        print("No opportunities found.")

if __name__ == "__main__":
    test_arbitrage()
