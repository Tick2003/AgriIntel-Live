import re
import pandas as pd
import random

class ChatbotEngine:
    """
    Handles 'WhatsApp-style' and Voice queries.
    Focus: Intent Detection & Entity Extraction for AgriIntel.in APIs.
    """
    def __init__(self, db_manager):
        self.db = db_manager
        
    def process_query_structured(self, query, context=None):
        """
        Parses query and returns {intent, entities, response_text}.
        If context is provided, it uses it to fill missing entities.
        """
        q = query.lower()
        context = context or {}
        
        # 1. Extract Entities
        commodity = self._extract_commodity(q) or context.get('crop')
        mandi = self._extract_mandi(q) or context.get('mandi')
        time_horizon = self._extract_time_horizon(q)
        
        # 2. Detect Intent
        intent = "unknown"
        if any(w in q for w in ["price", "rate", "bhav", "daam"]):
            intent = "price_query"
        elif any(w in q for w in ["forecast", "next week", "future", "ahead"]):
            intent = "forecast_query"
        elif any(w in q for w in ["advice", "sell", "hold", "suggest"]):
            intent = "sell_or_hold_advice"
        elif any(w in q for w in ["risk", "danger", "safe"]):
            intent = "risk_status"
        elif any(w in q for w in ["arbitrage", "profit", "other mandi", "different market"]):
            intent = "arbitrage_profitability"
        elif any(w in q for w in ["weather", "rain", "temperature"]):
            intent = "weather_impact"

        # 3. Formulate Response (Simulated data fetch for now)
        response_text = self._generate_response(intent, commodity, mandi, time_horizon)
        
        return {
            "intent": intent,
            "entities": {
                "commodity": commodity,
                "mandi": mandi,
                "time_horizon": time_horizon
            },
            "response_text": response_text
        }

    def _extract_commodity(self, text):
        crops = ["onion", "potato", "tomato", "rice", "wheat", "garlic", "ginger"]
        for c in crops:
            if c in text:
                return c.capitalize()
        return None

    def _extract_mandi(self, text):
        mandis = ["azadpur", "nasik", "cuttack", "bhubaneswar", "jatni", "pune", "lasalgaon"]
        for m in mandis:
            if m in text:
                return m.capitalize()
        return None

    def _extract_time_horizon(self, text):
        if "next week" in text: return "7_days"
        if "next month" in text: return "30_days"
        if "tomorrow" in text: return "1_day"
        return "current"

    def _generate_response(self, intent, commodity, mandi, time):
        if not commodity:
            return "Please name the crop you are asking about."
        
        mandi_str = f" in {mandi}" if mandi else " in nearby markets"
        
        if intent == "price_query":
            price = random.randint(2000, 4000)
            return f"The current price of {commodity}{mandi_str} is ₹{price} per quintal."
            
        if intent == "forecast_query":
            return f"Based on our AI analytics, {commodity} prices{mandi_str} are expected to rise by 5% next week."
            
        if intent == "sell_or_hold_advice":
            return f"Current recommendation for {commodity}: Hold. Prices are expected to strengthen."
            
        if intent == "risk_status":
            return f"Market risk for {commodity}{mandi_str} is Low (Score: 24/100)."
            
        return f"I understand you are asking about {commodity}. How can I help further?"
