import pandas as pd
import numpy as np

class AnomalyDetectionEngine:
    """
    AGENT 3 — SHOCK MONITORING AGENT
    Role: Detects anomalies and market shocks.
    Goal: Detect abnormal price movements by comparing actual prices with model predictions.
    """
    def __init__(self):
        pass

    def detect_shocks(self, actual_data: pd.DataFrame, forecast_data: pd.DataFrame) -> dict:
        """
        Compare actuals vs forecasts boundaries or just check for high volatility if forecast not historically aligned.
        For this MVP, we check if the latest actual price is within the confidence interval of the forecast 
        (assuming forecast was made for today - strictly speaking we'd need past forecasts, 
        but we'll simulate 'deviation from trend' here).
        
        Alternatively, we can just look solely at the latest price drop/rise > threshold.
        """
        if actual_data.empty:
            return {"alert": False, "message": "No data"}
            
        latest_price = actual_data['price'].iloc[-1]
        prev_price = actual_data['price'].iloc[-2] if len(actual_data) > 1 else latest_price
        
        pct_change = (latest_price - prev_price) / prev_price if prev_price != 0 else 0
        
        shock_detected = False
        severity = "None"
        score = 0
        
        # Simple threshold logic
        if abs(pct_change) > 0.15: # 15% change
            shock_detected = True
            severity = "High"
            score = 100
        elif abs(pct_change) > 0.05: # 5% change
            shock_detected = True
            severity = "Medium"
            score = 50
            
        return {
            "is_shock": shock_detected,
            "severity": severity,
            "score": score,
            "details": f"Price changed by {pct_change:.1%} recently."
        }
