
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

    def get_signal(self, current_price, forecast_df, risk_score, shock_info):
        """
        Determines the trading signal based on Forecast Trend, Risk, and Shocks.
        
        Returns:
            dict: {'signal': 'SELL', 'color': 'green', 'reason': '...'}
        """
        # 1. Calculate Forecast Trend (Slope of best fit line on forecast)
        dates = np.arange(len(forecast_df))
        prices = forecast_df['forecast_price'].values
        slope, _ = np.polyfit(dates, prices, 1)
        
        # Calculate expected % change
        future_avg = prices.mean()
        pct_change = ((future_avg - current_price) / current_price) * 100
        
        signal = "HOLD"
        color = "orange"
        reason = "Market is stable with no strong trend."
        
        # 2. Logic Tree
        
        # CRITICAL: If Shock Detected -> WAIT
        if shock_info['is_shock']:
            return {
                'signal': 'WAIT / RISKY',
                'color': 'red',
                'reason': f"Market in shock ({shock_info['severity']}). Volatility is too high to trade safely."
            }
            
        # HIGH RISK -> HOLD/WAIT
        if risk_score > 70:
            return {
                'signal': 'WAIT',
                'color': 'red',
                'reason': "Market risk is very high. Prices are unpredictable."
            }
            
        # STRONG UPTRNED -> HOLD (Wait for peak)
        if pct_change > 5 and slope > 0:
            return {
                'signal': 'HOLD',
                'color': 'orange',
                'reason': f"Prices are rising (+{pct_change:.1f}% expected). Hold stock for better returns."
            }
            
        # DOWNTREND -> SELL NOW
        if slope < 0:
            return {
                'signal': 'SELL NOW',
                'color': 'green',
                'reason': "Forecast shows a downward trend. Sell now to avoid loss."
            }
            
        # MODERATE UPTREND -> BUY/HOLD
        if 0 < pct_change <= 5:
            return {
                'signal': 'ACCUMULATE',
                'color': 'blue',
                'reason': "Slight upward trend. Good time to accumulate stock."
            }
            
        return {
            'signal': signal,
            'color': color,
            'reason': reason
        }

    def simulate_profit(self, current_price, forecast_df, quantity_quintals):
        """
        Simulates P&L for different time horizons.
        """
        scenarios = []
        
        # defined horizons
        horizons = [7, 15, 30]
        
        for days in horizons:
            if days <= len(forecast_df):
                # Get forecast for that day (approximate index)
                target_row = forecast_df.iloc[days-1]
                future_price = target_row['forecast_price']
                
                # P&L Calculation
                revenue_now = current_price * quantity_quintals
                revenue_future = future_price * quantity_quintals
                
                profit = revenue_future - revenue_now
                
                # Risk Adjustment (using confidence interval)
                # Worst case revenue
                revenue_worst = target_row['lower_bound'] * quantity_quintals
                profit_worst = revenue_worst - revenue_now
                
                scenarios.append({
                    'Horizon': f"{days} Days",
                    'Expected Price': future_price,
                    'Expected P&L': profit,
                    'Risk Adjusted P&L': profit_worst,
                    'Date': target_row['date'].date()
                })
                
        return pd.DataFrame(scenarios)
