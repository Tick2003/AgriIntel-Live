"""
database/signals.py — Signal Tracking Operations
==================================================
"""

import pandas as pd
import logging
from datetime import timedelta

from database.connection import get_connection

logger = logging.getLogger(__name__)


def log_signal(date, commodity, mandi, signal, price_at_signal):
    """Logs a decision signal."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            
            # Check if exists for this date/commodity/mandi
            c.execute("SELECT id FROM signal_logs WHERE date=? AND commodity=? AND mandi=?", (date, commodity, mandi))
            if c.fetchone():
                return # Already logged
                
            c.execute('''
                INSERT INTO signal_logs (date, commodity, mandi, signal, price_at_signal, price_after_7d, profitability_status)
                VALUES (?, ?, ?, ?, ?, NULL, NULL)
            ''', (date, commodity, mandi, signal, price_at_signal))
            conn.commit()
    except Exception as e:
        logger.error(f"log_signal failed: {e}")


def get_signal_stats(commodity, mandi):
    """
    Retrieves stats for 'Win Rate'. 
    Logic: 
    - Updates any NULL price_after_7d if data now exists.
    - Calculates profitability.
    """
    try:
        with get_connection() as conn:
            # 1. Update pending logs
            # Find logs > 7 days old with no outcome
            pending_df = pd.read_sql("SELECT * FROM signal_logs WHERE price_after_7d IS NULL", conn)
            
            if not pending_df.empty:
                c = conn.cursor()
                prices_df = pd.read_sql("SELECT date, price_modal FROM market_prices WHERE commodity=? AND mandi=?", conn, params=[commodity, mandi])
                # Fix date parsing if stored as mixed format, assume YYYY-MM-DD
                prices_df['date'] = pd.to_datetime(prices_df['date'], errors='coerce')
                
                for _, row in pending_df.iterrows():
                    try:
                        signal_date = pd.to_datetime(row['date'])
                        if pd.isna(signal_date): continue
                        
                        target_date = signal_date + timedelta(days=7)
                        
                        # Use nearest date match if exact date missing (robustness)
                        outcome_row = prices_df[prices_df['date'] >= target_date].sort_values('date').head(1)
                        
                        if not outcome_row.empty:
                            outcome_price = outcome_row['price_modal'].iloc[0]
                            price_now = row['price_at_signal']
                            signal = row['signal']
                            
                            status = "Neutral"
                            if signal == "SELL NOW":
                                if outcome_price < price_now: status = "Profitable"
                                else: status = "Loss"
                            elif (signal == "HOLD" or signal == "ACCUMULATE"):
                                if outcome_price > price_now: status = "Profitable"
                                else: status = "Loss"
                            elif signal == "WAIT / RISKY":
                                status = "N/A" # Neutral
                            else:
                                status = "Neutral"

                            c.execute("UPDATE signal_logs SET price_after_7d=?, profitability_status=? WHERE id=?", 
                                      (outcome_price, status, row['id']))
                    except Exception as e:
                        logger.error(f"Error processing log {row['id']}: {e}")
                        continue
                        
                conn.commit()

            # 2. Calculate Stats
            df = pd.read_sql("SELECT * FROM signal_logs WHERE commodity=? AND mandi=? AND profitability_status IS NOT NULL", conn, params=[commodity, mandi])
    except Exception as e:
        logger.error(f"get_signal_stats failed: {e}")
        return {"total": 0, "win_rate": 0, "profitable": 0}
    
    if df.empty:
        return {"total": 0, "win_rate": 0, "profitable": 0}
        
    total = len(df[df['profitability_status'] != 'N/A'])
    profitable = len(df[df['profitability_status'] == 'Profitable'])
    
    win_rate = (profitable / total * 100) if total > 0 else 0
    
    return {
        "total": total,
        "win_rate": win_rate,
        "profitable": profitable
    }
