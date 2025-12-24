import pandas as pd
import numpy as np
from datetime import timedelta
import xgboost as xgb
from sklearn.preprocessing import MinMaxScaler

class ForecastAgent:
    """
    AGENT 2 — FORECAST EXECUTION AGENT (ML-REAL)
    Role: Price Forecast Agent
    Goal: Train an XGBoost model on-the-fly to generate realistic 30-day forecasts.
    """
    def __init__(self):
        self.model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, learning_rate=0.1)

    def prepare_features(self, df):
        """
        Feature Engineering: Lags, Rolling Means, Date parts.
        """
        df = df.copy()
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        
        # Lag features
        df['lag_1'] = df['price'].shift(1)
        df['lag_7'] = df['price'].shift(7)
        
        # Rolling features
        df['rolling_mean_7'] = df['price'].rolling(window=7).mean()
        df['rolling_std_7'] = df['price'].rolling(window=7).std()
        
        return df.dropna()

    def generate_forecasts(self, data: pd.DataFrame, commodity: str, mandi: str) -> pd.DataFrame:
        """
        Generates 30-day forecast using XGBoost recursive strategy.
        """
        # Ensure data is sorted
        data = data.sort_values('date').copy()
        
        # Minimum data check
        if len(data) < 30:
            return self._generate_fallback(data, commodity, mandi)

        # 1. Train Model
        features_df = self.prepare_features(data)
        feature_cols = ['day_of_week', 'month', 'lag_1', 'lag_7', 'rolling_mean_7', 'rolling_std_7', 'arrival']
        
        # Mock 'arrival' for future if not present, assume mean
        if 'arrival' not in features_df.columns:
            features_df['arrival'] = 0
            
        X = features_df[feature_cols]
        y = features_df['price']
        
        self.model.fit(X, y)
        
        # 2. Recursive Forecast
        future_dates = []
        forecast_prices = []
        
        # append last known window to start recursion
        current_data = data.copy()
        
        last_date = data['date'].max()
        
        for i in range(1, 31):
            next_date = last_date + timedelta(days=i)
            
            # Create a temporary row for prediction features
            temp_df = current_data.copy()
            # Append a dummy row for next_date to calculate features
            next_row = pd.DataFrame([{
                'date': next_date, 
                'price': np.nan, # To be predicted
                'arrival': current_data['arrival'].mean() # Assume avg arrival
            }])
            temp_df = pd.concat([temp_df, next_row], ignore_index=True)
            
            # Engineer features
            temp_features = self.prepare_features(temp_df)
            
            # Get the exact row for prediction (the last one)
            pred_row = temp_features.tail(1)[feature_cols]
            
            # Predict
            pred_price = self.model.predict(pred_row)[0]
            
            # Store
            future_dates.append(next_date)
            forecast_prices.append(pred_price)
            
            # Update current_data with predicted value for next recursion
            # We strictly need to update the 'price' in the temp dataframe's last row and make it permanent
            next_row['price'] = pred_price
            current_data = pd.concat([current_data, next_row], ignore_index=True)
            
        # 3. Construct Result
        forecast_prices = np.array(forecast_prices)
        
        # Statistical Confidence Interval (Model doesn't give this directly without quantile reg)
        # We'll use the training RMSE or a simple heuristic
        std_dev = data['price'].std()
        lower_bound = forecast_prices - (std_dev * 0.5)
        upper_bound = forecast_prices + (std_dev * 0.5)
        
        return pd.DataFrame({
            'date': future_dates,
            'forecast_price': forecast_prices,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'commodity': commodity,
            'mandi': mandi
        })

    def _generate_fallback(self, data, commodity, mandi):
        """Original random walk Fallback"""
        last_date = pd.to_datetime(data['date'].max())
        last_price = data['price'].iloc[-1]
        future_dates = [last_date + timedelta(days=i) for i in range(1, 31)]
        np.random.seed(42)
        random_changes = np.random.normal(0, last_price * 0.02, 30)
        forecast_prices = last_price + np.cumsum(random_changes)
        confidence_interval = np.linspace(last_price * 0.05, last_price * 0.15, 30)
        return pd.DataFrame({
            'date': future_dates,
            'forecast_price': forecast_prices,
            'lower_bound': forecast_prices - confidence_interval,
            'upper_bound': forecast_prices + confidence_interval,
            'commodity': commodity,
            'mandi': mandi
        })
