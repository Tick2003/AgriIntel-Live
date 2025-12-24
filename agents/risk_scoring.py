import pandas as pd

class MarketRiskEngine:
    """
    AGENT 4 — RISK SCORING AGENT
    Role: Calculates overall market risk score (0-100).
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
            tags.append("Recent Shock Detected")
        if score > 70:
            tags.append("High Risk Factors")
        elif score > 30:
            tags.append("Moderate Risk Factors")
        else:
            tags.append("Low Risk Factors")
        return tags
```
