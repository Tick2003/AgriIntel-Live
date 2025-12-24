import pandas as pd
import numpy as np
from datetime import timedelta

class ForecastAgent:
    """
    AGENT 2 — FORECAST EXECUTION AGENT
    Role: Price Forecast Agent
    Goal: Run the latest trained ML model to generate 7, 14, and 30-day forecasts.
    """
    def __init__(self):
        pass

    def generate_forecasts(self, data: pd.DataFrame, commodity: str, mandi: str) -> pd.DataFrame:
        """
        Geneate mock forecasts for 30 days ahead.
        """
        last_date = pd.to_datetime(data['date'].max())
        last_price = data['price'].iloc[-1]
        
        future_dates = [last_date + timedelta(days=i) for i in range(1, 31)]
        
        # Generate some random walk data for forecast
        np.random.seed(42)
        random_changes = np.random.normal(0, last_price * 0.02, 30)
        forecast_prices = last_price + np.cumsum(random_changes)
        
        # Add confidence intervals
        confidence_interval = np.linspace(last_price * 0.05, last_price * 0.15, 30)
        
        forecast_df = pd.DataFrame({
            'date': future_dates,
            'forecast_price': forecast_prices,
            'lower_bound': forecast_prices - confidence_interval,
            'upper_bound': forecast_prices + confidence_interval,
            'commodity': commodity,
            'mandi': mandi
        })
        
        return forecast_df
