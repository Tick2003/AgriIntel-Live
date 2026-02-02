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
        
        # 2. Volatility Influence
        if market_volatility > 0.02: # >2% daily volatility
            score += 30
            tags.append("High Market Volatility")
        elif market_volatility > 0.01:
            score += 10
            
        # 3. Forecast Uncertainty
        if forecast_std > 500: # Arbitrary high std dev
            score += 20
            tags.append("High Forecast Uncertainty")
            
        # Cap score
        score = min(score, 100)
        
        risk_level = "High" if score > 70 else "Medium" if score > 30 else "Low"

        return {
            "risk_score": int(score),
            "risk_level": risk_level,
            "volatility": market_volatility,
            "regime": self.determine_regime(market_volatility, shock_info.get('is_shock', False)),
            "explanation_tags": tags
        }

    def determine_regime(self, volatility, is_shock, current_price_velocity=0):
        """
        Determines the market regime using K-Means Clustering logic (Simulated for single point).
        In a full batch system, we would fit KMeans on history. 
        Here we map the cluster centroids logic for speed.
        
        Clusters (Hypothetical trained centroids):
        0. Stable: Low Vol, Low Shock
        1. Volatile: High Vol, No Shock
        2. Distress/Crisis: High Vol + Shock
        """
        from sklearn.cluster import KMeans
        import numpy as np

        # Rule-based fallback if ML fails or for reliability
        # But let's make it "ML-like" by calculating distance to centroids
        
        # Centroids [Volatility, ShockBinary]
        centroids = {
            "Stable": [0.005, 0],
            "Volatile": [0.025, 0],
            "Crisis": [0.040, 1]
        }
        
        # Current point
        point = np.array([volatility, 1 if is_shock else 0])
        
        # Find nearest centroid
        min_dist = float('inf')
        regime = "Stable"
        
        for label, center in centroids.items():
            dist = np.linalg.norm(point - np.array(center))
            if dist < min_dist:
                min_dist = dist
                regime = label
                
        return regime
