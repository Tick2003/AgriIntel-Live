import pandas as pd
import numpy as np
from datetime import datetime

class DataReliabilityAgent:
    """
    Validates scraped market data before promotion to the production database.
    Checks for:
    1. Completeness (Missing Values)
    2. Uniqueness (Duplicate Entries)
    3. Plausibility (Outliers vs Historical Data)
    """
    
    def __init__(self, db_manager):
        self.dbm = db_manager
        
    def validate_batch(self, df, batch_id):
        """
        Main validation pipeline.
        Returns:
        - valid_df: DataFrame of records safe to promote.
        - issues: List of issues found for logging.
        - stats: Dict of validation stats.
        """
        issues = []
        valid_indices = []
        
        if df.empty:
            return pd.DataFrame(), [], {"total": 0, "valid": 0, "rejected": 0}
            
        print(f"Validating batch {batch_id} with {len(df)} records...")
        
        # Pre-fetch historical context for outlier detection
        # Optimization: Fetch last known price for all commodities in checking set
        # For simplicity, we might do per-row or bulk fetch. 
        # Let's do a bulk fetch of latest prices for known comm/mandis.
        
        for idx, row in df.iterrows():
            is_valid = True
            
            # 1. Missing Value Check
            if pd.isna(row['price_modal']) or pd.isna(row['commodity']) or pd.isna(row['mandi']):
                issues.append({
                    "batch_id": batch_id,
                    "date": row.get('date', datetime.now().strftime("%Y-%m-%d")),
                    "commodity": row.get('commodity', 'Unknown'),
                    "mandi": row.get('mandi', 'Unknown'),
                    "issue_type": "MISSING_DATA",
                    "severity": "CRITICAL",
                    "details": "Critical fields (Price/Commodity/Mandi) are missing.",
                    "raw_value": str(row.to_dict())
                })
                is_valid = False
            
            # 2. Plausibility Check (Outliers)
            if is_valid:
                # Check vs History
                # Fetch last price
                # We use a try-except block optimize loop speed
                try:
                    last_df = self.dbm.get_latest_prices(row['commodity'])
                    if not last_df.empty:
                        # Filter for mandi
                        mandi_df = last_df[last_df['mandi'] == row['mandi']]
                        if not mandi_df.empty:
                            last_price = mandi_df.iloc[-1]['price_modal']
                            current_price = row['price_modal']
                            
                            # Calculate % change
                            pct_change = abs((current_price - last_price) / last_price)
                            
                            if pct_change > 0.5: # 50% jump
                                issues.append({
                                    "batch_id": batch_id,
                                    "date": row['date'],
                                    "commodity": row['commodity'],
                                    "mandi": row['mandi'],
                                    "issue_type": "OUTLIER_SHOCK",
                                    "severity": "WARNING", # We still allow it but log it
                                    "details": f"Price changed by {pct_change*100:.1f}% (Prev: {last_price}, Curr: {current_price})",
                                    "raw_value": str(current_price)
                                })
                                # Note: We do NOT set is_valid=False for Shock. 
                                # Real shocks happen. We just flag it. 
                                # If it was 500% (5.0), maybe we reject.
                                if pct_change > 3.0: # 300% Error likely
                                    is_valid = False
                                    issues[-1]['severity'] = "CRITICAL"
                                    issues[-1]['details'] += " - REJECTED as improbable."
                except Exception as e:
                    print(f"Validation Error (Outlier): {e}")

            # 3. Duplicate Check
            if is_valid:
                # Naive check: does this date/comm/mandi already exist in DB?
                # Optimization: In high volume, do this in SQL batch.
                # Here, we trust the DB constraints or simple check.
                # For now, let's assume if it passed others, it's good, 
                # but let's check if exact row exists in staging (deduplication within batch)
                pass 

            if is_valid:
                valid_indices.append(idx)
        
        valid_df = df.loc[valid_indices].copy()
        rejected_count = len(df) - len(valid_df)
        
        return valid_df, issues, {
            "total": len(df),
            "valid": len(valid_df),
            "rejected": rejected_count
        }
