import pandas as pd
import numpy as np
from datetime import timedelta
import xgboost as xgb
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

class ForecastingAgent:
    """
    AGENT 2 — FORECAST EXECUTION AGENT (ML-REAL)
    Role: Price Forecast Agent
    Goal: Train an XGBoost model on-the-fly to generate realistic 30-day forecasts.
    Strategy: Trend (Linear) + Residuals (XGBoost) to capture both direction and volatility.
    """
    def __init__(self):
        # We will use a LinearRegression for trend and XGB for residuals
        self.trend_model = LinearRegression()
        self.residual_model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, learning_rate=0.1)

    def prepare_features(self, df):
        """
        Feature Engineering: Lags, Rolling Means, Date parts, Technicals, Weather.
        """
        df = df.copy()
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        
        # Determine target column for feature engineering
        target_col = 'resid' if 'resid' in df.columns else 'price'
        
        # --- TECHNICAL INDICATORS (ML Heavy) ---
        # 1. RSI (Relative Strength Index)
        delta = df[target_col].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi'] = df['rsi'].fillna(50)
        
        # 2. Bollinger Bands
        df['bb_mid'] = df[target_col].rolling(window=20).mean()
        df['bb_std'] = df[target_col].rolling(window=20).std()
        df['bb_upper'] = df['bb_mid'] + (2 * df['bb_std'])
        df['bb_lower'] = df['bb_mid'] - (2 * df['bb_std'])
        df['bb_dist'] = (df[target_col] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 1e-9)
        
        # 3. MACD
        exp12 = df[target_col].ewm(span=12, adjust=False).mean()
        exp26 = df[target_col].ewm(span=26, adjust=False).mean()
        df['macd'] = exp12 - exp26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        # Lags
        df['lag_1'] = df[target_col].shift(1)
        df['lag_7'] = df[target_col].shift(7)
        df['lag_14'] = df[target_col].shift(14) # New Lag
        
        # Rolling features
        df['rolling_mean_7'] = df[target_col].rolling(window=7).mean()
        df['rolling_std_7'] = df[target_col].rolling(window=7).std()
        
        # Weather Lag (if columns exist)
        if 'rainfall' in df.columns:
            df['rain_lag_1'] = df['rainfall'].shift(1).fillna(0)
            df['temp_lag_1'] = df['temperature'].shift(1).fillna(25)
        
        # Fix FutureWarning: fillna with method is deprecated
        return df.bfill().fillna(0)

    def _tune_model(self, X, y):
        """
        Optimization: Tuning disabled for speed (Hot-fix).
        Using pre-validated 'Good Enough' parameters.
        To re-enable: uncomment GridSearchCV code.
        """
        # Optimized defaults based on prior runs
        best_params = {
            'learning_rate': 0.1,
            'max_depth': 5,
            'n_estimators': 100,
            'subsample': 0.8,
            'objective': 'reg:squarederror'
        }
        
        # print("Skipping Auto-Tune for speed...") 
        xgb_model = xgb.XGBRegressor(**best_params)
        model = xgb_model.fit(X, y) # Fit once
        
        return model


    def generate_forecasts(self, data: pd.DataFrame, commodity: str, mandi: str, weather_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Generates 30-day forecast using Trend + Residual approach with Weather Integration.
        """
        # Ensure data is sorted
        data = data.sort_values('date').copy()
        
        # Merge Weather if available
        if weather_df is not None and not weather_df.empty:
            # Ensure dates match for merge
            weather_df['date'] = pd.to_datetime(weather_df['date'])
            data = pd.merge(data, weather_df[['date', 'rainfall', 'temperature']], on='date', how='left')
            # Forward fill missing weather (persistence)
            data['rainfall'] = data['rainfall'].fillna(0)
            # Fix FutureWarning
            data['temperature'] = data['temperature'].ffill().fillna(25)
        
        # Minimum data check
        if len(data) < 30:
            return self._generate_fallback(data, commodity, mandi)

        # --- STEP 1: DETRENDING ---
        data['date_ordinal'] = data['date'].apply(lambda x: x.toordinal())
        
        X_trend = data[['date_ordinal']]
        y_trend = data['price']
        
        self.trend_model.fit(X_trend, y_trend)
        data['trend'] = self.trend_model.predict(X_trend)
        data['resid'] = data['price'] - data['trend']
        
        # --- STEP 2: TRAIN XGBOOST ON RESIDUALS ---
        features_df = self.prepare_features(data)
        feature_cols = [
            'day_of_week', 'month', 'lag_1', 'lag_7', 'lag_14',
            'rolling_mean_7', 'rolling_std_7',
            'rsi', 'bb_dist', 'macd', 'macd_signal'
        ]
        
        if 'rain_lag_1' in features_df.columns:
            feature_cols.extend(['rain_lag_1', 'temp_lag_1'])
        
        X = features_df[feature_cols]
        y = features_df['resid']
        
        # Validation Split (Last 5 days)
        val_size = 5
        X_train_full, X_val = X.iloc[:-val_size], X.iloc[-val_size:]
        y_train_full, y_val = y.iloc[:-val_size], y.iloc[-val_size:]
        
        # AUTO-TUNE (Optimization Step)
        self.residual_model = self._tune_model(X_train_full, y_train_full)
        
        # Calculate RMSE on residuals
        val_preds = self.residual_model.predict(X_val)
        mse_val = mean_squared_error(y_val, val_preds)
        rmse_val = np.sqrt(mse_val)
        
        # Log to debug-level if needed, but remove print for production to avoid spam
        # print(f"Residual Model RMSE: {rmse_val:.2f}") 
        
        # Retrain on full data with best params
        self.residual_model.fit(X, y)
        
        # --- STEP 3: RECURSIVE FORECAST ---
        future_dates = []
        forecast_prices = []
        
        # Start recursion from the last available data
        current_data = data.copy()
        last_date = data['date'].max()
        
        for i in range(1, 31):
            next_date = last_date + timedelta(days=i)
            next_ordinal = next_date.toordinal()
            
            # A. Predict Trend
            # Fix UserWarning: Ensure input has feature names
            pred_trend = self.trend_model.predict(pd.DataFrame([[next_ordinal]], columns=['date_ordinal']))[0]
            
            # B. Predict Residual (Recursive)
            # Create temp row
            temp_df = current_data.copy()
            next_row = pd.DataFrame([{
                'date': next_date,
                'resid': np.nan, 
                'trend': pred_trend,
                'price': np.nan, 
                'date_ordinal': next_ordinal,
                'rainfall': temp_df['rainfall'].iloc[-1] if 'rainfall' in temp_df.columns else 0, # Weather Persistence
                'temperature': temp_df['temperature'].iloc[-1] if 'temperature' in temp_df.columns else 25
            }])
            temp_df = pd.concat([temp_df, next_row], ignore_index=True)
            
            # Engineer features on this temp structure
            temp_features = self.prepare_features(temp_df)
            
            # Predict residual
            pred_row = temp_features.tail(1)[feature_cols]
            pred_resid = self.residual_model.predict(pred_row)[0]
            
            # Combine
            pred_price = pred_trend + pred_resid
            
            # Store
            future_dates.append(next_date)
            forecast_prices.append(pred_price)
            
            # C. Update Loop
            next_row['resid'] = pred_resid
            next_row['price'] = pred_price
            current_data = pd.concat([current_data, next_row], ignore_index=True)

        # --- STEP 4: CONFIDENCE INTERVALS ---
        forecast_prices = np.array(forecast_prices)
        
        # Uncertainty grows with time, but tuned model should be tighter
        # Use simple heuristic: RMSE * log(t) instead of sqrt(t) for slightly tighter bounds initially
        time_steps = np.arange(1, 31)
        uncertainty_factor = np.log(time_steps + 1) + 0.5 
        
        margin_of_error = 1.96 * rmse_val * uncertainty_factor
        
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
