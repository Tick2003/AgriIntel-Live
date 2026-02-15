
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.db_manager import get_forecast_vs_actuals, log_model_metrics

class PerformanceMonitor:
    """
    AGENT 10 — PERFORMANCE MONITOR
    Role: Quality Assurance
    Goal: Track model accuracy (MAPE, RMSE, MAE) and Model Health.
    """
    def __init__(self):
        self.degradation_threshold = 15.0 # MAPE > 15% is degraded

    def calculate_health_score(self, mape, recent_trend_mape):
        """
        Computes a 0-100 health score.
        Base score starts at 100.
        Penalties:
        - High Correlation to Error (MAPE)
        - Degradation (Recent > Historic)
        """
        score = 100
        
        # 1. Accuracy Penalty
        # If MAPE is 0%, score 100. If MAPE is 20%, score 60.
        # Formula: 100 - (MAPE * 2)
        score -= (mape * 2)
        
        # 2. Degradation Penalty
        # If recent trend is worse than overall, deduct points
        if recent_trend_mape > mape * 1.2: # 20% degradation
            score -= 10
            
        return max(0, min(100, score))

    def update_metrics(self, commodity, mandi):
        """
        Calculates and logs performance metrics for a specific market.
        Returns the calculated metrics dict.
        """
        df = get_forecast_vs_actuals(commodity, mandi)
        
        if df.empty:
            return None
            
        # Ensure we sort by date
        df = df.sort_values('target_date')
        
        # 1. Calculate Overall Metrics (All Time)
        # Assuming 'error' and 'error_pct' are already in df from db_manager
        # If not, calc them:
        if 'error' not in df.columns:
            df['error'] = df['predicted_price'] - df['actual_price']
            df['error_pct'] = (df['error'].abs() / df['actual_price']) * 100
            
        # 2. Key Metrics
        n = len(df)
        mape = df['error_pct'].mean()
        rmse = np.sqrt((df['error'] ** 2).mean())
        mae = df['error'].abs().mean()
        
        # 3. Rolling / Recent Metrics (Last 30 days for Health Score)
        recent_df = df.tail(30)
        recent_mape = recent_df['error_pct'].mean() if len(recent_df) > 0 else mape
        
        # 4. Health Score
        health_score = self.calculate_health_score(mape, recent_mape)
        
        # 5. Signal Accuracy (Directional Accuracy)
        # Did it predict the correct direction vs previous day?
        # Complex to calc without prev day actuals in this view. 
        # For now, we will use a simpler proxy: % of errors < 10%
        accurate_preds = len(df[df['error_pct'] < 10.0])
        signal_accuracy = (accurate_preds / n * 100) if n > 0 else 0
        
        # 6. Log to DB
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        try:
            log_model_metrics(
                date=today_str,
                commodity=commodity,
                mandi=mandi,
                mape=round(mape, 2),
                rmse=round(rmse, 2),
                mae=round(mae, 2),
                health_score=round(health_score, 1),
                accuracy=round(signal_accuracy, 1),
                sample_size=n
            )
            print(f"Logged metrics for {commodity}-{mandi}: Health={health_score:.1f}, MAPE={mape:.1f}%")
        except Exception as e:
            print(f"Error logging metrics: {e}")
            
        return {
            "mape": round(mape, 2),
            "rmse": round(rmse, 2),
            "mae": round(mae, 2),
            "health_score": round(health_score, 1),
            "n": n
        }

    def get_rolling_metrics(self, commodity, mandi, window=30):
        """Used for UI charts."""
        df = get_forecast_vs_actuals(commodity, mandi)
        if df.empty: return pd.DataFrame()
        
        # ... logic to rolling aggregate if needed, or just return raw df for UI to plot
        return df

if __name__ == "__main__":
    pm = PerformanceMonitor()
    # Test
    # pm.update_metrics("Onion", "Lasalgaon")
