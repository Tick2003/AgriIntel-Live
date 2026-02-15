
import sys
import os
sys.path.append(os.getcwd())
from agents.risk_scoring import MarketRiskEngine

def test_risk_breakdown():
    engine = MarketRiskEngine()
    
    # Test Case 1: High Volatility, Neutral Sentiment
    print("--- Test Case 1: High Volatility ---")
    res1 = engine.calculate_risk_score(
        shock_info={"is_shock": False}, 
        forecast_std=100, 
        market_volatility=0.03, # High
        sentiment_score=0,
        arrival_anomaly=0,
        weather_risk=0
    )
    print(res1)
    
    # Test Case 2: Shock + Bad Weather + Negative Sentiment
    print("\n--- Test Case 2: Shock + Weather + Sentiment ---")
    res2 = engine.calculate_risk_score(
        shock_info={"is_shock": True, "severity": "Medium"}, 
        forecast_std=600, 
        market_volatility=0.01, 
        sentiment_score=-0.8, # Negative
        arrival_anomaly=0.6, # High arrivals
        weather_risk=1.0 # Bad weather
    )
    print(res2)

    # Verify breakdown keys
    if "breakdown" in res1 and "breakdown" in res2:
        print("\n✅ Risk Breakdown Dictionary Present.")
    else:
        print("\n❌ Breakdown Missing.")

if __name__ == "__main__":
    test_risk_breakdown()
