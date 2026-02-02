
import pandas as pd
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from agents.forecast_execution import ForecastingAgent
from app.utils import get_live_data

def verify_forecast():
    print("Fetching data...")
    # Get data for a known commodity
    data = get_live_data("Potato", "Agra")
    print(f"Data fetched: {len(data)} rows")
    
    if len(data) < 30:
        print("Not enough data to verify fully.")
        return

    print("Initializing Agent...")
    agent = ForecastingAgent()
    
    print("Generating Forecast...")
    forecast = agent.generate_forecasts(data, "Potato", "Agra")
    
    print("\nForecast Result (First 5):")
    print(forecast[['date', 'forecast_price', 'lower_bound', 'upper_bound']].head())
    
    # Check if forecast is flat
    prices = forecast['forecast_price'].values
    std_dev = prices.std()
    print(f"\nForecast Standard Deviation: {std_dev:.4f}")
    
    if std_dev < 1.0:
        print("WARNING: Forecast appears flat (or very low variance). Check trend logic.")
    else:
        print("SUCCESS: Forecast shows variance (Trend/Seasonality active).")

    # Check Bounds
    margin_start = (forecast['upper_bound'].iloc[0] - forecast['lower_bound'].iloc[0]) / 2
    margin_end = (forecast['upper_bound'].iloc[-1] - forecast['lower_bound'].iloc[-1]) / 2
    
    print(f"Margin of Error Start: {margin_start:.2f}")
    print(f"Margin of Error End: {margin_end:.2f}")
    
    if margin_end > margin_start:
        print("SUCCESS: Uncertainty increases over time.")
    else:
        print("WARNING: Uncertainty does not increase over time.")

if __name__ == "__main__":
    verify_forecast()
