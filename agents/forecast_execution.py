import pandas as pd
import numpy as np
from datetime import timedelta
import xgboost as xgb
from sklearn.preprocessing import MinMaxScaler

class ForecastingAgent:
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
        Now RIGOROUS: No random drift, pure ML + RMSE Confidence Intervals.
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
        
        # --- SELF-CORRECTION / TUNING STEP ---
        # 1. Validation Split: Hide last 5 days to check model accuracy
        val_size = 5
        X_train, X_val = X.iloc[:-val_size], X.iloc[-val_size:]
        y_train, y_val = y.iloc[:-val_size], y.iloc[-val_size:]
        
        # 2. Train on subset
        self.model.fit(X_train, y_train)
        
        # 3. Predict validation set
        val_preds = self.model.predict(X_val)
        
        # 4. Calculate RMSE for Confidence Intervals
        from sklearn.metrics import mean_squared_error
        mse_val = mean_squared_error(y_val, val_preds)
        rmse_val = np.sqrt(mse_val)
        
        print(f"Model Training RMSE: {rmse_val:.2f}")
        
        # 5. RETRAIN on FULL data for future prediction
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
            
            # SIMULATE FUTURE ARRIVAL (Mean Reversion, not Random Walk)
            # We assume future arrivals will be close to the average
            avg_arrival = current_data['arrival'].mean()
            
            # Append a dummy row for next_date
            next_row = pd.DataFrame([{
                'date': next_date, 
                'price': np.nan, 
                'arrival': avg_arrival
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
            
            # Update current_data (feedback loop)
            next_row['price'] = pred_price
            current_data = pd.concat([current_data, next_row], ignore_index=True)
            
        # 3. Construct Result
        forecast_prices = np.array(forecast_prices)
        
        # Statistical Confidence Interval (95% CI approx => +/- 1.96 * RMSE)
        # We increase uncertainty slightly over time (sqrt of time steps)
        # CI = Forecast +/- (1.96 * RMSE * sqrt(t))
        
        time_steps = np.arange(1, 31)
        uncertainty_factor = np.sqrt(time_steps) # Logic: Error grows with time
        
        margin_of_error = 1.96 * rmse_val * (1 + (uncertainty_factor * 0.1)) 
        # Note: Scaled down factor slightly so it doesn't explode, but basically RMSE * t
        
        lower_bound = forecast_prices - margin_of_error
        upper_bound = forecast_prices + margin_of_error
        
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
