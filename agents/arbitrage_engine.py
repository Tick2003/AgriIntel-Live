
import pandas as pd

class ArbitrageAgent:
    """
    AGENT 7 — REGIONAL ARBITRAGE AGENT
    Role: Logistics Optimizer
    Goal: Identify profitable trade routes between Mandis.
    """
    def __init__(self):
        # Mock Distance Matrix (km)
        self.distances = {
            ('Azadpur', 'Pune'): 1400, ('Azadpur', 'Kolar'): 2100, ('Azadpur', 'Indore'): 800,
            ('Pune', 'Kolar'): 900, ('Pune', 'Indore'): 600, ('Indore', 'Kolar'): 1300,
            ('Agra', 'Azadpur'): 230, ('Agra', 'Indore'): 600, ('Cuttack', 'Azadpur'): 1700
        }
        self.default_dist = 500 # Fallback

    def get_distance(self, m1, m2):
        if m1 == m2: return 0
        return self.distances.get((m1, m2)) or self.distances.get((m2, m1)) or self.default_dist

    def find_opportunities(self, current_commodity, current_mandi, all_data_df, shock_status_current, 
                         cost_config=None):
        """
        Scans for price gaps > real transport cost.
        cost_config: {fuel_rate: 15, toll: 500, labor: 200, spoilage: 0.05}
        """
        # Default Config
        cfg = cost_config or {}
        fuel_rate = cfg.get('fuel_rate', 0.02) # INR/km/kg -> ~20 INR/km/ton
        toll = cfg.get('toll', 200) # Fixed per trip (amortized)
        labor = cfg.get('labor', 100) # Loading/Unloading per Quintal
        spoilage = cfg.get('spoilage', 0.05) # 5% loss
        
        # Smart Filter: Avoid noise if current market is already unstable
        if shock_status_current.get('is_shock'):
            return pd.DataFrame() 
            
        if all_data_df.empty:
            return pd.DataFrame()

        # Get latest price for the current mandi
        current_row = all_data_df[(all_data_df['mandi'] == current_mandi) & 
                                  (all_data_df['commodity'] == current_commodity)].sort_values('date').tail(1)
        
        if current_row.empty:
            return pd.DataFrame()
            
        my_price = current_row['price'].iloc[-0]
        
        # Get latest prices for ALL other mandis
        latest_prices = all_data_df[all_data_df['commodity'] == current_commodity].sort_values('date').groupby('mandi').tail(1)
        
        opportunities = []
        min_margin = 50 
        
        for _, row in latest_prices.iterrows():
            target_mandi = row['mandi']
            target_price = row['price']
            
            if target_mandi == current_mandi: continue

            dist = self.get_distance(current_mandi, target_mandi)
            
            # Cost Model (Per Quintal)
            # 1 ton truck = 10 Quintals. Fuel/km = 20Rs. Dist=500km -> 10000Rs. Per Q = 1000Rs.
            # Simplified: Fuel Rate is per km per Quintal? No, usually per km for truck.
            # Let's assume passed fuel_rate is INR per km PER QUINTAL (approx 2.0)
            transport_cost = (dist * fuel_rate) + (toll / 10) + labor # Amortize toll
            
            # Spoilage Loss (Value lost)
            loss_val = my_price * spoilage
            
            total_cost = transport_cost + loss_val
            
            # Net Profit
            gross_margin = target_price - my_price
            net_profit = gross_margin - total_cost
            
            # Sensitivity (Risk)
            # What if Target Price drops 10%?
            target_price_bear = target_price * 0.90
            profit_bear = (target_price_bear - my_price) - total_cost
            
            confidence = "High" if profit_bear > 0 else "Medium" if net_profit > 200 else "Low"

            if net_profit > min_margin:
                opportunities.append({
                    'Type': 'Sell to',
                    'Target Mandi': target_mandi,
                    'Distance (km)': dist,
                    'Current Price': float(my_price),
                    'Target Price': float(target_price),
                    'Total Cost': round(total_cost, 0),
                    'Net Profit/Qt': round(net_profit, 2),
                    'Profit (Bear Case)': round(profit_bear, 2),
                    'Confidence': confidence,
                    'Action': f"🚛 > {target_mandi}"
                })

        # Return sorted
        result_df = pd.DataFrame(opportunities)
        if not result_df.empty:
            result_df = result_df.sort_values('Net Profit/Qt', ascending=False)
            
        return result_df
