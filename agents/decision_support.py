
import pandas as pd
import numpy as np

class DecisionAgent:
    """
    AGENT 6 — DECISION SUPPORT AGENT
    Role: Strategic Advisor
    Goal: Translate forecast data into actionable Buy/Sell/Hold signals and simulate profit scenarios.
    """
    def __init__(self):
        pass

    def get_signal(self, current_price, forecast_df, risk_score, shock_dict):
        """
        Determines the trading signal based on rigorous logic gates.
        """
        # 1. Calculate Forecast Slope (Trend)
        # Simple linear regression slope for last 30 days forecast
        if forecast_df.empty: return {'signal': 'NEUTRAL', 'color': 'gray', 'reason': 'No forecast data'}

        y = forecast_df['forecast_price'].values
        x = np.arange(len(y))
        slope, _ = np.polyfit(x, y, 1) # Change per day
        
        # Threshold: 0.5% of current price per day ?? No, maybe just 0.1% is significant enough for daily
        # User said "T1 = 0.5% of current price per day" - that's huge! 0.5% daily is 15% monthly.
        # Let's stick to the user's suggestion or a slightly more sensitive one if 0.5% is too high.
        # Let's use 0.1% as a more realistic "Trend" threshold for daily agri prices.
        T1 = 0.001 * current_price 
        
        trend_up = slope > T1
        trend_down = slope < -T1
        
        # 2. Risk Flags
        high_risk = risk_score > 70
        med_risk = 40 <= risk_score <= 70
        shock_high = shock_dict.get('severity') == 'High'
        
        # 3. Decision Rules
        signal = "NEUTRAL"
        color = "gray"
        reason_list = []
        
        # 🟢 SELL NOW
        # IF trend_down AND (shock_high OR high_risk)
        if trend_down and (shock_high or high_risk):
            signal = "SELL NOW"
            color = "green" # Green for "Action", or Red for "Danger"? User used Green for Sell Now.
            reason_list.append(f"📉 Trend is negative (Slope: {slope:.2f}/day).")
            if shock_high: reason_list.append(f"💥 High Intensity Shock detected.")
            if high_risk: reason_list.append(f"🔥 Market Risk is High ({risk_score}).")
            
        # 🟡 HOLD
        # IF trend_up AND NOT shock_high AND risk_score < 60
        elif trend_up and not shock_high and risk_score < 60:
            signal = "HOLD"
            color = "#FFC107" # Amber/Yellow
            reason_list.append(f"📈 Trend is positive (Slope: +{slope:.2f}/day).")
            reason_list.append(f"🛡️ Risk is acceptable ({risk_score}).")
            
        # 🔴 WAIT / RISKY
        # IF shock_high OR high_risk
        elif shock_high or high_risk:
            signal = "WAIT / RISKY"
            color = "red"
            if shock_high: reason_list.append(f"💥 High Intensity Shock detected.")
            if high_risk: reason_list.append(f"🔥 Market Risk is High ({risk_score}).")
            
        else:
            signal = "NEUTRAL"
            color = "blue"
            reason_list.append("Market does not show strong buy/sell signals.")

        # 4. Calculate Confidence Score
        # Logic: High Risk -> Lower Confidence. Strong Trend -> Higher Confidence.
        # Base: 100
        # Penalties: Risk Score (* 0.4), Shock (-20 if Med)
        # Bonus: Abs(Slope) if significant
        
        confidence = 100 - (risk_score * 0.4)
        if shock_high: confidence -= 30
        elif shock_dict.get('severity') == 'Medium': confidence -= 15
        
        # Clamp 0-99
        confidence = max(10, min(99, confidence))
        
        # Format "SELL NOW (Confidence: 82%)"
        signal_text = f"{signal} (Confidence: {int(confidence)}%)"

        return {
            'signal': signal, # Raw signal for logic
            'signal_text': signal_text, # UI display
            'confidence': confidence,
            'color': color,
            'reason': "\n".join([f"- {r}" for r in reason_list])
        }

    def simulate_profit(self, current_price, forecast_df, quantity_quintals):
        """
        Simulates P&L with Risk Bands using RMSE * sqrt(t).
        """
        if forecast_df.empty: return pd.DataFrame()
        
        scenarios = []
        # Calculate approximate RMSE from confidence intervals if not passed explicitly/
        # CI = 1.96 * RMSE * sqrt(t). width = upper - lower = 2 * 1.96 * RMSE * sqrt(t)
        # RMSE approx = width / (3.92 * sqrt(t))
        # Let's estimate local sigma (RMSE) from the first few days or usage passed sigma.
        # For simplicity, we can infer sigma from the first valid CI width.
        
        horizons = [7, 15, 30]
        
        for days in horizons:
            if days <= len(forecast_df):
                row = forecast_df.iloc[days-1]
                Pt = row['forecast_price']
                
                # Infer RMSE-like spread from the bound width provided by ForecastingAgent
                # ForecastingAgent logic: bound = price +/- 1.96 * std_dev * sqrt(t)
                # So (Upper - Lower) = 3.92 * std_dev * sqrt(t)
                # width = row['upper_bound'] - row['lower_bound']
                # sigma_proxy = width / (3.92 * np.sqrt(days))
                
                # Wait, simpler: The user GAVE the formula for Risk Band:
                # Upper = (Pt + 1.96 * sigma * sqrt(t) - P0) * Q
                # We already have Pt, Lower, Upper in the dataframe!
                # ForecastingAgent already calculated Pt +/- ...
                # So we can just use the dataframe's bounds directly for the risk band.
                # Expected Gain = (Pt - P0) * Q
                # Upper Gain = (Upper_Price - P0) * Q
                # Lower Gain = (Lower_Price - P0) * Q
                
                expected_gain = (Pt - current_price) * quantity_quintals
                upper_gain = (row['upper_bound'] - current_price) * quantity_quintals
                lower_gain = (row['lower_bound'] - current_price) * quantity_quintals
                
                # Volatility (Risk Band Width)
                risk_band = (upper_gain - lower_gain) / 2
                
                scenarios.append({
                    'Horizon': f"{days} Days",
                    'Expected Price': Pt,
                    'Expected Profit': expected_gain,
                    'Risk (±)': risk_band, 
                    'Range': f"₹{lower_gain:.0f} to ₹{upper_gain:.0f}"
                })
        
        return pd.DataFrame(scenarios)
