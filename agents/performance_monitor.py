import pandas as pd
import numpy as np
from datetime import timedelta
import sys
import os

# Add root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.db_manager import get_forecast_vs_actuals, log_model_metrics, get_latest_prices
from agents.forecast_execution import ForecastingAgent

class PerformanceMonitor:
    """
    AGENT 10 — PERFORMANCE MONITOR
    Role: Quality Assurance
    Goal: Track model accuracy (MAPE, RMSE) and Signal Win Rates.
    """
    def __init__(self):
        pass

    def calculate_metrics(self, commodity, mandi):
        """
        Calculates MAPE and RMSE based on logged forecasts vs actuals.
        Returns dict with metrics.
        """
        df = get_forecast_vs_actuals(commodity, mandi)
        
        if df.empty:
            return {
                "mape": 0.0,
                "rmse": 0.0,
                "n": 0
            }
            
        # Calculate Rolling MAPE (Last 30 samples)
        recent_df = df.tail(30)
        
        if len(recent_df) > 0:
            mape = (recent_df['error_pct'].mean())
            rmse = np.sqrt((recent_df['error'] ** 2).mean())
        else:
            mape = 0.0
            rmse = 0.0
            
        return {
            "mape": round(mape, 2),
            "rmse": round(rmse, 2),
            "n": len(recent_df)
        }

    def run_backtest(self, commodity, mandi, days=30):
        """
        Simulates a backtest by training on past data and predicting 'future' (which is now known).
        """
        # 1. Get Full History
        prices_df = get_latest_prices(commodity)
        prices_df = prices_df[prices_df['mandi'] == mandi].sort_values('date')
        
        if len(prices_df) < (30 + days):
            return {"status": "Failed", "reason": "Insufficient Data"}
            
        # 2. Split
        cutoff_date = prices_df['date'].max() - timedelta(days=days)
        train_df = prices_df[prices_df['date'] <= cutoff_date]
        test_df = prices_df[prices_df['date'] > cutoff_date]
        
        if test_df.empty:
             return {"status": "Failed", "reason": "No test data after split"}
        
        # 3. Forecast
        agent = ForecastingAgent()
        forecast_df = agent.generate_forecasts(train_df, commodity, mandi)
        
        # 4. Compare
        # Merge forecast (date) with test_df (date)
        # Ensure string/datetime match
        forecast_df['date'] = pd.to_datetime(forecast_df['date'])
        test_df = test_df.copy() # Avoid SettingWithCopy
        test_df['date'] = pd.to_datetime(test_df['date'])
        
        merged = pd.merge(test_df, forecast_df, on='date', how='inner')
        
        if merged.empty:
            return {"status": "Failed", "reason": "Date mismatch in backtest"}
            
        merged['error'] = merged['predicted_price'] - merged['price_modal'] if 'predicted_price' in merged.columns else merged['forecast_price'] - merged['price_modal']
        merged['error_abs'] = merged['error'].abs()
        merged['error_pct'] = (merged['error_abs'] / merged['price_modal']) * 100
        
        mape = merged['error_pct'].mean()
        rmse = np.sqrt((merged['error'] ** 2).mean())
        
        return {
            "status": "Success",
            "mape": round(mape, 2),
            "rmse": round(rmse, 2),
            "plot_data": merged[['date', 'price_modal', 'forecast_price']].to_dict('records')
        }

if __name__ == "__main__":
    pm = PerformanceMonitor()
    print(pm.calculate_metrics("Potato", "Agra"))
