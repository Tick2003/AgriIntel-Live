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

    def calculate_hold_duration(self, current_price, forecast_trend):
        """
        Advises how long to hold the crop based on forecast probability.
        """
        # Simple Logic: If trend is up, hold. If flat/down, sell.
        # forecast_trend is list of next 7 days prices
        
        if not forecast_trend or len(forecast_trend) < 3:
            return "Insufficient Data"
            
        start_price = current_price
        max_price = max(forecast_trend)
        max_day = forecast_trend.index(max_price) + 1
        
        profit_potential = ((max_price - start_price) / start_price) * 100
        
        if profit_potential > 5:
            return f"Hold for {max_day} days. Price expected to rise by {profit_potential:.1f}%."
        elif profit_potential > 1:
            return f"Hold for {max_day} days. Slight increase expected ({profit_potential:.1f}%)."
        else:
            return "Sell Now. No significant price rise expected soon."

    def get_chat_response(self, user_query, context_data):
        """
        Advanced Intent-Based Chat Engine with 'Senior Analyst' Persona.
        Context Data contains: signal, price, commodity, mandi, risk_score, sentiment, regime
        """
        q = user_query.lower()
        
        # EXTRACT CONTEXT
        signal = context_data.get('signal', 'NEUTRAL')
        conf = context_data.get('confidence', 0)
        risk_score = context_data.get('risk_score', 0)
        regime = context_data.get('regime', 'Unknown')
        sentiment_label = context_data.get('sentiment', 'Neutral')
        curr_price = context_data.get('current_price', 0)
        
        # PERSONA HEADER
        analyst_intro = "🤖 **AgriIntel.in Analyst**: "
        
        # --- INTENT 1: TRADING ADVICE ---
        if any(w in q for w in ['sell', 'buy', 'hold', 'advice', 'strategy', 'do']):
            
            # Construct a nuanced argument
            tone = "cautious" if risk_score > 50 else "confident"
            
            response = f"""
            {analyst_intro} Based on my analysis, the current strategy is **{signal}**.
            
            **📊 key Market Indicators:**
            *   **Market Regime**: {regime}
            *   **Risk Score**: {risk_score}/100 ({tone})
            *   **News Sentiment**: {sentiment_label}
            *   **Model Confidence**: {int(conf)}%
            
            **💡 Recommendation:**
            {context_data.get('reason', 'Trends suggest following the signal.')}
            """
            return response

        # --- INTENT 2: PRICE & FORECAST ---
        if any(w in q for w in ['price', 'forecast', 'tomorrow', 'future', 'trend']):
            return f"""
            {analyst_intro} The market is currently trading at **₹{curr_price:.2f}**.
            
            Our 30-day forecast models (XGBoost + Trend) indicate **{regime}** behavior ahead. 
            Please check the **Price Forecast** tab for the detailed projection curve and confidence intervals.
            """

        # --- INTENT 3: SCENARIOS (What-If) ---
        if 'rain' in q or 'flood' in q:
            sim = self.run_scenario(curr_price, 'heavy_rain')
            return f"""
            {analyst_intro} **Simulation Result: Heavy Rain Event** 🌧️
            
            Historical data suggests heavy rainfall disrupts supply chains immediately.
            *   **projected Impact**: {sim['change_pct']}
            *   **Target Price**: ₹{sim['new_price']:.2f}
            
            *Reasoning: {sim['reason']}*
            """
            
        if 'policy' in q or 'ban' in q or 'export' in q:
            sim = self.run_scenario(curr_price, 'export_ban')
            return f"""
            {analyst_intro} **Simulation Result: Export Ban** 🚫
            
            An export ban typically creates an immediate local oversupply.
            *   **Projected Impact**: {sim['change_pct']}
            *   **Target Price**: ₹{sim['new_price']:.2f}
            
            *Reasoning: {sim['reason']}*
            """

        # --- INTENT 4: SENTIMENT / NEWS ---
        if 'news' in q or 'sentiment' in q or 'mood' in q:
            return f"""
            {analyst_intro} The current market sentiment is **{sentiment_label}**.
            This is derived from analyzing recent headlines using our NLP engine. A {sentiment_label} mood often precedes {'price increases' if 'Bullish' in sentiment_label else 'price corrections'}.
            """

        # DEFAULT FALLBACK
        return f"{analyst_intro} I am ready to analyze the market. You can ask me about **Trading Signals**, **Price Trends**, **Market Scenarios** (e.g., 'Effect of rain'), or **News Sentiment**."
