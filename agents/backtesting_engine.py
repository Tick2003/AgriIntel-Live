
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.db_manager import get_price_history, get_historical_signals

class BacktestEngine:
    """
    AGENT 11 — BACKTESTING ENGINE
    Role: Simulator
    Goal: Simulate Buy/Sell strategies on historical data to estimate profitability.
    """
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.commission_pct = 0.005 # 0.5% per trade

    def simulate_forecasts(self, prices_df):
        """
        Since we might lack historical forecasts, generate 'Simulated Forecasts'
        using a simple moving average crossover strategy as a proxy for the ML model's trend detection.
        This allows testing the Decision Engine logic even without old logs.
        """
        df = prices_df.copy()
        # Proxy Logic:
        # If MA(7) > MA(30) -> Bullish Forecast (Slope Positive)
        # If MA(7) < MA(30) -> Bearish Forecast (Slope Negative)
        
        df['MA7'] = df['price_modal'].rolling(window=7).mean()
        df['MA30'] = df['price_modal'].rolling(window=30).mean()
        
        # Simulated "Forecast Slope"
        # If MA7 > MA30, assume model would predict +10 slope. Else -10.
        df['simulated_slope'] = np.where(df['MA7'] > df['MA30'], 10, -10)
        
        return df

    def run_backtest(self, commodity, mandi, start_date=None, end_date=None):
        """
        Runs the simulation.
        Returns:
        - daily_stats: DataFrame of daily portfolio value
        - metrics: Dict of Sharpe, Drawdown, Win Rate
        - trades: DataFrame of executed trades
        """
        # 1. Fetch History
        prices = get_price_history(commodity, mandi, start_date, end_date)
        if prices.empty:
            return None, {"error": "No data found"}, None
            
        prices['date'] = pd.to_datetime(prices['date'])
        prices = prices.sort_values('date').reset_index(drop=True)
        
        # 2. Setup Loop
        cash = self.initial_capital
        holdings = 0 # in Quintals
        equity_curve = []
        trades = []
        
        # 3. Signals source
        # Ideally use real logs, else simulate
        real_signals = get_historical_signals(commodity, mandi)
        use_simulation = real_signals.empty
        
        if use_simulation:
            # Generate simulated indicators
            sim_df = self.simulate_forecasts(prices)
        else:
            real_signals['date'] = pd.to_datetime(real_signals['date'])
        
        for idx, row in prices.iterrows():
            date = row['date']
            price = row['price_modal']
            
            signal = "HOLD"
            
            if use_simulation:
                # Sim Strategy: 
                # Buy if MA7 crosses above MA30 (Golden Cross)
                # Sell if MA7 crosses below MA30 (Death Cross)
                slope = sim_df.loc[idx, 'simulated_slope']
                # Determine transition?
                # For simplicity, just check current state
                prev_slope = sim_df.loc[idx-1, 'simulated_slope'] if idx > 0 else slope
                
                if slope > 0 and prev_slope <= 0:
                    signal = "BUY"
                elif slope < 0 and prev_slope >= 0:
                    signal = "SELL"
            else:
                # Look for real signal on this date
                match = real_signals[real_signals['date'] == date]
                if not match.empty:
                    sig_str = match.iloc[0]['signal'].upper()
                    if "BUY" in sig_str: signal = "BUY"
                    elif "SELL" in sig_str: signal = "SELL"
            
            # Execute Trade
            trade_val = 0
            if signal == "BUY" and cash > 0:
                # Buy Max
                qty = (cash * 0.99) / price # Reserve 1% for fees/slippage
                cost = qty * price
                comm = cost * self.commission_pct
                cash -= (cost + comm)
                holdings += qty
                trades.append({
                    "date": date, "type": "BUY", "price": price, "qty": qty, "value": cost, "comm": comm
                })
                
            elif signal == "SELL" and holdings > 0:
                # Sell All
                revenue = holdings * price
                comm = revenue * self.commission_pct
                cash += (revenue - comm)
                trades.append({
                    "date": date, "type": "SELL", "price": price, "qty": holdings, "value": revenue, "comm": comm
                })
                holdings = 0
                
            # Track Equity
            total_val = cash + (holdings * price)
            equity_curve.append({
                "date": date,
                "strategy_equity": total_val,
                "price": price
            })
            
        # 4. Calculate Metrics
        df_equity = pd.DataFrame(equity_curve)
        if df_equity.empty: return None, {"error": "Run failed"}, None

        # Benchmark: Buy and Hold
        initial_price = df_equity.iloc[0]['price']
        final_price = df_equity.iloc[-1]['price']
        bnh_return = ((final_price - initial_price) / initial_price) * 100
        
        # Strategy Return
        final_equity = df_equity.iloc[-1]['strategy_equity']
        strat_return = ((final_equity - self.initial_capital) / self.initial_capital) * 100
        
        # Drawdown
        df_equity['peak'] = df_equity['strategy_equity'].cummax()
        df_equity['drawdown'] = (df_equity['strategy_equity'] - df_equity['peak']) / df_equity['peak']
        max_drawdown = df_equity['drawdown'].min() * 100
        
        # Sharpe (Daily Batches)
        df_equity['returns'] = df_equity['strategy_equity'].pct_change()
        mean_ret = df_equity['returns'].mean()
        std_ret = df_equity['returns'].std()
        sharpe = (mean_ret / std_ret * np.sqrt(252)) if std_ret > 0 else 0
        
        # Win Rate
        df_trades = pd.DataFrame(trades)
        win_rate = 0
        if not df_trades.empty:
            # Match Buy/Sells to find round trip profits
            # Simplified: Just count profitable Sell trades relative to avg buy price? 
            # Or just assume standard FIFO. 
            # For this simplified version, let's just output raw trade count.
            pass

        metrics = {
            "Total Return": strat_return,
            "Benchmark Return": bnh_return,
            "Max Drawdown": max_drawdown,
            "Sharpe Ratio": sharpe,
            "Trade Count": len(df_trades),
            "Final Equity": final_equity
        }
        
        return df_equity, metrics, df_trades

if __name__ == "__main__":
    be = BacktestEngine()
    print(be.run_backtest("Onion", "Lasalgaon"))
