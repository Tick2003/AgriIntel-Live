import pandas as pd

class MarketRiskEngine:
    """
    AGENT 4 — RISK SCORING AGENT
    Role: Calculates overall market risk score (0-100).
    Goal: Assess current market risk based on volatility, forecast uncertainty, and detected shocks.
    """
    def __init__(self):
        pass

    def calculate_risk_score(self, shock_info: dict, forecast_std: float, market_volatility: float, 
                           sentiment_score: float = 0, arrival_anomaly: float = 0, weather_risk: float = 0) -> dict:
        """
        Decomposes risk into 4 components:
        1. Volatility (Price instability)
        2. Shock (Sudden anomalies)
        3. Sentiment (Market mood)
        4. External Factors (Arrivals + Weather)
        
        Returns Total Score (0-100) and Breakdown.
        """
        # 1. Volatility Risk (0-30 pts)
        # 2% vol = Max Risk
        vol_risk = min((market_volatility / 0.02) * 30, 30)
        
        # 2. Shock/Model Risk (0-30 pts)
        shock_risk = 0
        if shock_info.get("is_shock"):
            shock_risk = 30 if shock_info["severity"] == "High" else 15
        elif forecast_std > 500:
             shock_risk += 10
        shock_risk = min(shock_risk, 30)

        # 3. Sentiment Risk (0-20 pts)
        # Negative sentiment (Bearish) = Risk for farmers (Price drop)
        # Positive sentiment (Bullish) = Stability? Or also deviation?
        # Let's assume High Magnitude Sentiment = higher volatility risk.
        sent_risk = abs(sentiment_score) * 20
        
        # 4. External Risk (Arrivals + Weather) (0-20 pts)
        # High arrival surge (>50%) = Price Crash Risk
        arr_risk = min((max(arrival_anomaly, 0) / 0.5) * 10, 10)
        # Weather (0-10)
        w_risk = weather_risk * 10
        ext_risk = arr_risk + w_risk
        
        total_score = vol_risk + shock_risk + sent_risk + ext_risk
        total_score = min(total_score, 100)
        
        risk_level = "Critical" if total_score > 75 else "High" if total_score > 50 else "Moderate" if total_score > 25 else "Stable"

        return {
            "risk_score": int(total_score),
            "risk_level": risk_level,
            "regime": self.determine_regime(market_volatility, shock_info.get('is_shock', False)),
            "breakdown": {
                "Volatility": int(vol_risk),
                "Market Shocks": int(shock_risk),
                "News Sentiment": int(sent_risk),
                "Supply/Weather": int(ext_risk)
            },
            "explanation_tags": self._get_tags(vol_risk, shock_risk, sent_risk, ext_risk)
        }

    def _get_tags(self, v, s, n, e):
        tags = []
        if v > 20: tags.append("High Volatility")
        if s > 15: tags.append("Market Shock Detected")
        if n > 15: tags.append("Strong Sentiment Driver")
        if e > 15: tags.append("Supply/Weather Stress")
        return tags

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
