import pandas as pd
import sqlite3
import os
import sys

# Ensure root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DB_NAME

class UserProfileAgent:
    """
    AGENT 6 — USER PROFILE AGENT
    Role: Personalization Manager
    Goal: Store and retrieve user context (Risk Preference, Transport Cost).
    """
    def __init__(self, user_id="default_user"):
        self.user_id = user_id
        self._ensure_table()

    def _ensure_table(self):
        """Double check table exists (Development safety)"""
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_config (
                user_id TEXT PRIMARY KEY,
                risk_tolerance TEXT DEFAULT 'Medium',
                transport_cost REAL DEFAULT 0.0,
                default_mandi TEXT,
                default_commodity TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def get_profile(self):
        """Fetch user profile as dictionary."""
        conn = sqlite3.connect(DB_NAME)
        try:
            df = pd.read_sql(f"SELECT * FROM user_config WHERE user_id = '{self.user_id}'", conn)
            if df.empty:
                # Create default
                self.update_profile()
                return self.get_profile()
            return df.iloc[0].to_dict()
        finally:
            conn.close()

    def update_profile(self, risk_tolerance="Medium", transport_cost=0.0, default_mandi=None, default_commodity=None):
        """Upsert user profile."""
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Check if exists
        c.execute(f"SELECT 1 FROM user_config WHERE user_id = ?", (self.user_id,))
        exists = c.fetchone()
        
        if exists:
            query = """
                UPDATE user_config 
                SET risk_tolerance=?, transport_cost=?, default_mandi=?, default_commodity=?
                WHERE user_id=?
            """
            c.execute(query, (risk_tolerance, transport_cost, default_mandi, default_commodity, self.user_id))
        else:
            query = """
                INSERT INTO user_config (user_id, risk_tolerance, transport_cost, default_mandi, default_commodity)
                VALUES (?, ?, ?, ?, ?)
            """
            c.execute(query, (self.user_id, risk_tolerance, transport_cost, default_mandi, default_commodity))
            
        conn.commit()
        conn.close()
        return True
