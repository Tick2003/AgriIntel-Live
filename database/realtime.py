"""
database/realtime.py — Intraday Trades & RACE Ensemble Weights
================================================================
"""

import logging
from datetime import datetime, timedelta

import pandas as pd

from database.connection import get_connection

logger = logging.getLogger(__name__)


# --- Intraday Trades ---

def save_intraday_trade(trade_dict):
    """Save a single intraday trade to the database."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute(
                """INSERT INTO intraday_trades (timestamp, commodity, mandi, price, quantity, trade_type)
                   VALUES (:timestamp, :commodity, :mandi, :price, :quantity, :trade_type)""",
                trade_dict,
            )
            conn.commit()
    except Exception as e:
        logger.error(f"save_intraday_trade failed: {e}")


def get_latest_intraday_trades(commodity=None, mandi=None, limit=50):
    """Fetch the latest intraday trades."""
    try:
        with get_connection() as conn:
            query = "SELECT * FROM intraday_trades"
            conditions = []
            params = []
            if commodity:
                conditions.append("commodity = ?")
                params.append(commodity)
            if mandi:
                conditions.append("mandi = ?")
                params.append(mandi)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            df = pd.read_sql(query, conn, params=params)
            return df
    except Exception as e:
        logger.error(f"get_latest_intraday_trades failed: {e}")
        return pd.DataFrame()


def clear_old_intraday_trades(hours=24):
    """Remove intraday trades older than specified hours."""
    try:
        cutoff = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM intraday_trades WHERE timestamp < ?", (cutoff,))
            conn.commit()
            logger.info(f"Cleared intraday trades older than {hours} hours")
    except Exception as e:
        logger.error(f"clear_old_intraday_trades failed: {e}")


# --- RACE Ensemble Weights ---

def log_ensemble_weights(date, commodity, mandi, regime, model_weights, cv_mapes):
    """Log RACE ensemble model weights for tracking weight evolution."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            for model_name, weight in model_weights.items():
                mape = cv_mapes.get(model_name, 0)
                c.execute(
                    """INSERT INTO ensemble_weights_log (date, commodity, mandi, regime, model_name, weight, cv_mape)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (date, commodity, mandi, regime, model_name, weight, mape),
                )
            conn.commit()
    except Exception as e:
        logger.error(f"log_ensemble_weights failed: {e}")


def get_ensemble_weight_history(commodity, mandi, limit=30):
    """Retrieve recent ensemble weight evolution."""
    try:
        with get_connection() as conn:
            df = pd.read_sql(
                """SELECT * FROM ensemble_weights_log
                   WHERE commodity=? AND mandi=?
                   ORDER BY date DESC LIMIT ?""",
                conn,
                params=[commodity, mandi, limit * 4]
            )
            return df
    except Exception as e:
        logger.error(f"get_ensemble_weight_history failed: {e}")
        return pd.DataFrame()
