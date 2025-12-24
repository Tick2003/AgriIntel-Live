import pandas as pd

class RiskScoringAgent:
    """
    AGENT 4 — RISK SCORING AGENT
    Role: Market Risk Assessment Agent
    Goal: Assess current market risk based on volatility, forecast uncertainty, and detected shocks.
    """
    def __init__(self):
        pass

    def calculate_risk_score(self, shock_info: dict, forecast_std: float, market_volatility: float) -> dict:
        """
        Combine signals into a risk score.
        """
        risk_level = "Low"
        score = 0
        tags = []

        # 1. Shock Influence
        if shock_info.get("is_shock"):
            if shock_info["severity"] == "High":
                score += 50
                tags.append("Recent Severe Shock")
            else:
                score += 20
                tags.append("Recent Shock")
        
        # 2. Volatility Influence (Mock logic)
        if market_volatility > 0.3: # High vol
            score += 30
            tags.append("High Market Volatility")
        elif market_volatility > 0.1:
            score += 10
            
        # 3. Forecast Uncertainty
        if forecast_std > 500: # Arbitrary high std dev
            score += 20
            tags.append("High Forecast Uncertainty")
            
        # Cap score
        score = min(score, 100)
        
        if score > 70:
            risk_level = "High"
        elif score > 30:
            risk_level = "Medium"
            
        return {
            "risk_score": score,
            "risk_level": risk_level,
            "explanation_tags": tags
        }
