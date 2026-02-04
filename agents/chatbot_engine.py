import re
import pandas as pd
import random

class ChatbotEngine:
    """
    Handles 'WhatsApp-style' short queries.
    Focus: Simplicity, Direct Data Fetching, Vernacular Intent (simulated)
    """
    def __init__(self, db_manager):
        self.db = db_manager
        
    def process_query(self, query):
        """
        Parses query, fetches data, constructs response.
        """
        q = query.lower()
        
        # 1. Identify Intent & Entities
        commodity = self._extract_commodity(q)
        mandi = self._extract_mandi(q)
        
        if not commodity:
            return "Please mention a crop (e.g., Onion, Tomato)."
            
        if not mandi:
            # If no mandi, assume a default or ask (here we default to Azadpur for demo)
            mandi = "Azadpur" 
            
        # 2. Fetch Data
        # In real app, query DB. Here, we simulate/fetch latest.
        # We can try to use db_manager or just mock for reliability if DB is empty
        price = random.randint(2000, 4000)
        trend = random.choice(["Rising", "Falling", "Stable"])
        
        # 3. Formulate Response
        if "price" in q or "rate" in q or "bhav" in q:
            return self._format_price_response(commodity, mandi, price, trend)
            
        if "advice" in q or "sell" in q:
            return f"For {commodity} in {mandi}, market is {trend}. {'Sell now' if trend == 'Falling' else 'Hold for 2 days'}."
            
        # Default price check
        return self._format_price_response(commodity, mandi, price, trend)

    def _extract_commodity(self, text):
        crops = ["onion", "potato", "tomato", "rice", "wheat"]
        for c in crops:
            if c in text:
                return c.capitalize()
        return None

    def _extract_mandi(self, text):
        mandis = ["azadpur", "nasik", "cuttack", "bhubaneswar", "jatni"]
        for m in mandis:
            if m in text:
                return m.capitalize()
        return None

    def _format_price_response(self, comm, mandi, price, trend):
        return f"📍 *{mandi} Mandi Update*\n🥔 {comm}: ₹{price}/q\n📈 Trend: {trend}\n\n_Updated: Just now_"
