import pandas as pd
import numpy as np

class DataHealthAgent:
    """
    AGENT 1 — DATA HEALTH AGENT
    Role: Data Health Monitoring Agent
    Goal: Monitor agricultural market datasets for missing data, abnormal zeros, or sudden breaks.
    """
    def __init__(self):
        pass

    def check_daily_completeness(self, data: pd.DataFrame) -> dict:
        """
        Check for missing days and data quality.
        Expects a DataFrame with 'date', 'price', and 'arrival' columns.
        """
        if data.empty:
            return {"status": "Critical", "message": "No data available."}

        # Check for missing dates
        data['date'] = pd.to_datetime(data['date'])
        full_date_range = pd.date_range(start=data['date'].min(), end=data['date'].max())
        missing_dates = full_date_range.difference(data['date'])
        
        missing_pct = len(missing_dates) / len(full_date_range)
        
        # Check for zeros in price
        zeros_pct = (data['price'] == 0).mean()

        status = "OK"
        issues = []

        if missing_pct > 0.1:
            status = "Warning"
            issues.append(f"{len(missing_dates)} missing days ({missing_pct:.1%})")
        if missing_pct > 0.3:
            status = "Critical"
        
        if zeros_pct > 0.05:
            status = "Warning" if status == "OK" else status
            issues.append(f"{zeros_pct:.1%} days with zero price")

        return {
            "status": status,
            "missing_days": len(missing_dates),
            "issues": issues
        }
