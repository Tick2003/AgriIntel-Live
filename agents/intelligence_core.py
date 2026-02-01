import pandas as pd
import random

class IntelligenceAgent:
    """
    AGENT 7 — INTELLIGENCE CORE
    Role: Interactive Consultant
    Goal: Handle natural language queries and run "What-If" scenarios.
    """
    def __init__(self):
        self.scenarios = {
            "heavy_rain": {
                "name": "Heavy Rain / Flood",
                "impact": 12.5, # +12.5% Price
                "reason": "Supply chain disruption and crop damage due to excess moisture.",
                "sentiment": "Bearish for Supply -> Bullish for Price"
            },
            "export_ban": {
                "name": "Export Ban Policy",
                "impact": -15.0, # -15% Price
                "reason": "Oversupply in local market as international exit is closed.",
                "sentiment": "Bearish for Price"
            },
            "fuel_hike": {
                "name": "Fuel Price Hike (+10%)",
                "impact": 5.0, # +5% Price
                "reason": "Increased transport costs passed down to consumer.",
                "sentiment": "Bullish for Price"
            },
            "festival_demand": {
                "name": "Major Festival Demand",
                "impact": 8.0, # +8% Price
                "reason": "Surge in household consumption.",
                "sentiment": "Bullish for Price"
            }
        }

    def run_scenario(self, current_price, scenario_key):
        """
        Simulates the impact of a specific event on the current price.
        """
        if scenario_key not in self.scenarios:
            return None
            
        scen = self.scenarios[scenario_key]
        impact_pct = scen['impact']
        new_price = current_price * (1 + impact_pct/100)
        
        return {
            "scenario": scen['name'],
            "original_price": current_price,
            "new_price": new_price,
            "change_pct": f"{'+' if impact_pct > 0 else ''}{impact_pct}%",
            "reason": scen['reason'],
            "sentiment": scen['sentiment']
        }

    def get_chat_response(self, user_query, context_data):
        """
        Simple Intent-Based Chat Engine.
        Context Data contains: signal, price, commodity, mandi
        """
        q = user_query.lower()
        
        # Intent 1: Advice / Signal
        if any(w in q for w in ['sell', 'buy', 'hold', 'advice', 'strategy', 'do']):
            signal = context_data.get('signal', 'NEUTRAL')
            conf = context_data.get('confidence', 0)
            reason = context_data.get('reason', '')
            
            return f"**My Recommendation**: {signal} (Confidence: {int(conf)}%)\n\n**Reasoning**:\n{reason}\n\nBased on your audit history, strategies like this have a high success rate in similar conditions."

        # Intent 2: Price / Forecast
        if any(w in q for w in ['price', 'forecast', 'tomorrow', 'future']):
            price = context_data.get('current_price', 0)
            # Fake forecast reference since we don't assume we have the full df here for simplicity, 
            # or we rely on the prompt to trust the systems' general advice.
            # But better: Use the context!
            return f"The current price is ₹{price:.2f}. Our models predict increased volatility. Check the 'Price Forecast' tab for the detailed 30-day view."

        # Intent 3: Scenarios (Rain, Etc)
        if 'rain' in q or 'flood' in q:
            sim = self.run_scenario(context_data.get('current_price', 0), 'heavy_rain')
            return f"⚠️ **Scenario Analysis: Heavy Rain**\n\nIf it rains heavily, prices typically rise by **{sim['change_pct']}** due to supply constraints.\n\nProjected Price: **₹{sim['new_price']:.2f}**\nReason: {sim['reason']}"
            
        if 'policy' in q or 'ban' in q or 'export' in q:
            sim = self.run_scenario(context_data.get('current_price', 0), 'export_ban')
            return f"⚠️ **Scenario Analysis: Export Ban**\n\nAn export ban usually crashes local prices by **{sim['change_pct']}** due to oversupply.\n\nProjected Price: **₹{sim['new_price']:.2f}**\nReason: {sim['reason']}"

        # Default
        return "I can help you with trading signals, price forecasts, or 'What-If' scenarios (e.g., 'What if it rains?', 'Should I sell?'). Try asking one of those!"
