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
        Feature Engineering: Lags, Rolling Means, Date parts.
        """
        df = df.copy()
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        
        # Determine target column for feature engineering
        # If 'resid' exists, we are training/predicting residuals.
        # If not (e.g. initial setup), we default to 'price' but logic below handles 'resid' primarily.
        target_col = 'resid' if 'resid' in df.columns else 'price'
        
        df['lag_1'] = df[target_col].shift(1)
        df['lag_7'] = df[target_col].shift(7)
        
        # Rolling features
        df['rolling_mean_7'] = df[target_col].rolling(window=7).mean()
        df['rolling_std_7'] = df[target_col].rolling(window=7).std()
        
        return df.dropna()

    def generate_forecasts(self, data: pd.DataFrame, commodity: str, mandi: str) -> pd.DataFrame:
        """
        Generates 30-day forecast using Trend + Residual approach.
        """
        # Ensure data is sorted
        data = data.sort_values('date').copy()
        
        # Minimum data check
        if len(data) < 30:
            return self._generate_fallback(data, commodity, mandi)

        # --- STEP 1: DETRENDING ---
        # Convert date to ordinal for regression
        data['date_ordinal'] = data['date'].apply(lambda x: x.toordinal())
        
        X_trend = data[['date_ordinal']]
        y_trend = data['price']
        
        self.trend_model.fit(X_trend, y_trend)
        data['trend'] = self.trend_model.predict(X_trend)
        data['resid'] = data['price'] - data['trend']
        
        # --- STEP 2: TRAIN XGBOOST ON RESIDUALS ---
        features_df = self.prepare_features(data)
        feature_cols = ['day_of_week', 'month', 'lag_1', 'lag_7', 'rolling_mean_7', 'rolling_std_7']
        
        X = features_df[feature_cols]
        y = features_df['resid']
        
        # Validation Split (Last 5 days)
        val_size = 5
        X_train, X_val = X.iloc[:-val_size], X.iloc[-val_size:]
        y_train, y_val = y.iloc[:-val_size], y.iloc[-val_size:]
        
        self.residual_model.fit(X_train, y_train)
        
        # Calculate RMSE on residuals
        val_preds = self.residual_model.predict(X_val)
        mse_val = mean_squared_error(y_val, val_preds)
        rmse_val = np.sqrt(mse_val)
        
        print(f"Residual Model RMSE: {rmse_val:.2f}")
        
        # Retrain on full data
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
            pred_trend = self.trend_model.predict([[next_ordinal]])[0]
            
            # B. Predict Residual (Recursive)
            # Create temp row
            temp_df = current_data.copy()
            next_row = pd.DataFrame([{
                'date': next_date,
                'resid': np.nan, # To be filled
                'trend': pred_trend,
                'price': np.nan, # Placeholder
                'date_ordinal': next_ordinal
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
        
        # Uncertainty grows with time (Trend uncertainty + Residual uncertainty)
        # Simplified: Use Residual RMSE * sqrt(t)
        time_steps = np.arange(1, 31)
        uncertainty_factor = np.sqrt(time_steps)
        
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
