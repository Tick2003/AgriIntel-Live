
import pandas as pd

class ArbitrageAgent:
    """
    AGENT 7 — REGIONAL ARBITRAGE AGENT
    Role: Logistics Optimizer
    Goal: Identify profitable trade routes between Mandis.
    """
    def __init__(self):
        # Simulated transport cost matrix (or flat rate)
        # In reality, this would be a distance matrix API
        self.flat_transport_cost_per_km = 5 # INR per km (just a placeholder multiplier)
        # Or simpler: Fixed cost per Quintal between known hubs
        self.avg_transport_cost = 150 # INR per Quintal (approx for inter-state)

    def find_opportunities(self, current_commodity, current_mandi, all_data_df):
        """
        Scans for price gaps > transport cost.
        """
        if all_data_df.empty:
            return pd.DataFrame()

        # Get latest price for the current mandi
        current_row = all_data_df[(all_data_df['mandi'] == current_mandi) & 
                                  (all_data_df['commodity'] == current_commodity)].sort_values('date').tail(1)
        
        if current_row.empty:
            return pd.DataFrame()
            
        my_price = current_row['price'].iloc[-0]
        
        # Get latest prices for ALL other mandis for same commodity
        latest_prices = all_data_df[all_data_df['commodity'] == current_commodity].sort_values('date').groupby('mandi').tail(1)
        
        opportunities = []
        
        for _, row in latest_prices.iterrows():
            target_mandi = row['mandi']
            target_price = row['price']
            
            if target_mandi == current_mandi:
                continue
                
            # Logic: Can I buy here and sell there?
            # Profit = Sell Price - (Buy Price + Transport)
            
            # Case 1: Sell to Target (if I hold stock)
            gross_margin = target_price - my_price
            net_profit = gross_margin - self.avg_transport_cost
            
            if net_profit > 0:
                opportunities.append({
                    'Type': 'Sell to',
                    'Target Mandi': target_mandi,
                    'Current Price': f"₹{my_price:.0f}",
                    'Target Price': f"₹{target_price:.0f}",
                    'Net Profit/Qt': net_profit,
                    'Action': f"🚛 Move stock to {target_mandi}"
                })
                
            # Case 2: Buy from Target (if I am a trader)
            # Profit = My Price - (Target Price + Transport)
            buy_margin = my_price - target_price
            buy_profit = buy_margin - self.avg_transport_cost
            
            if buy_profit > 0:
                opportunities.append({
                    'Type': 'Buy from',
                    'Target Mandi': target_mandi,
                    'Current Price': f"₹{my_price:.0f}",
                    'Target Price': f"₹{target_price:.0f}",
                    'Net Profit/Qt': buy_profit,
                    'Action': f"🛒 Source from {target_mandi}"
                })
                
        # Return sorted by profit
        result_df = pd.DataFrame(opportunities)
        if not result_df.empty:
            result_df = result_df.sort_values('Net Profit/Qt', ascending=False)
            
        return result_df
