import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.data_health import DataHealthAgent
from agents.forecast_execution import ForecastAgent
from agents.shock_monitoring import ShockMonitoringAgent
from agents.risk_scoring import RiskScoringAgent
from agents.explanation_report import ExplanationAgent
from app.utils import get_live_data, load_css, get_news_feed, get_weather_data, get_db_options

# Page Config
st.set_page_config(page_title="AgriIntel", layout="wide", page_icon="🌾")
st.markdown(load_css(), unsafe_allow_html=True)

# Title
st.title("🌾 Agricultural Market Intelligence System")
st.markdown("---")

# Sidebar
st.sidebar.header("Configuration")

# Dynamic options from DB
db_commodities, db_mandis = get_db_options()

selected_commodity = st.sidebar.selectbox("Select Commodity", db_commodities, index=0)
selected_mandi = st.sidebar.selectbox("Select Mandi", db_mandis, index=0)

# Initialize Agents
@st.cache_resource
def load_agents():
    return {
        "health": DataHealthAgent(),
        "forecast": ForecastAgent(),
        "shock": ShockMonitoringAgent(),
        "risk": RiskScoringAgent(),
        "explain": ExplanationAgent()
    }

agents = load_agents()

# Load Data
data = get_live_data(selected_commodity, selected_mandi)
last_date = data['date'].max().strftime('%Y-%m-%d')
st.caption(f"Data Source: Agmarknet (Simulated) | Last Updated: {last_date}")

# Run Agents
health_status = agents["health"].check_daily_completeness(data)
forecast_df = agents["forecast"].generate_forecasts(data, selected_commodity, selected_mandi)
shock_info = agents["shock"].detect_shocks(data, forecast_df)
risk_info = agents["risk"].calculate_risk_score(shock_info, forecast_df['forecast_price'].std(), data['price'].pct_change().std())
explanation = agents["explain"].generate_explanation(selected_commodity, risk_info, shock_info, forecast_df)

# Navigation
page = st.sidebar.radio("Navigate", ["Market Overview", "Price Forecast", "Risk & Shocks", "Compare Markets", "News & Insights", "Model Performance", "Explanation & Insights"])

# --- PAGE 1: MARKET OVERVIEW ---
if page == "Market Overview":
    st.header(f"Market Overview: {selected_commodity} in {selected_mandi}")
    
    # Weather Widget
    weather_df = get_weather_data()
    if not weather_df.empty:
        # Simple random pick for demo or based on logic if region mapped
        w = weather_df.iloc[-1] 
        st.info(f"⛈️ **Weather Alert**: {w['condition']} | Temp: {w['temperature']}°C | Rainfall: {w['rainfall']}mm")
    
    col1, col2, col3 = st.columns(3)
    current_price = data['price'].iloc[-1]
    prev_price = data['price'].iloc[-2]
    delta = current_price - prev_price
    
    col1.metric("Current Price", f"₹{current_price:.2f}", f"{delta:.2f}")
    col2.metric("Daily Arrivals", f"{data['arrival'].iloc[-1]} tons")
    col3.metric("Data Health", health_status['status'], delta_color="off" if health_status['status'] == "OK" else "inverse")
    
    st.subheader("Historical Price Trend")
    fig = px.line(data, x='date', y='price', title='Price History (90 Days)')
    st.plotly_chart(fig, use_container_width=True)

# --- PAGE 2: PRICE FORECAST ---
elif page == "Price Forecast":
    st.header("Price Forecast (Next 30 Days)")
    
    fig = go.Figure()
    
    # Historical
    fig.add_trace(go.Scatter(x=data['date'], y=data['price'], mode='lines', name='Historical'))
    
    # Forecast
    fig.add_trace(go.Scatter(x=forecast_df['date'], y=forecast_df['forecast_price'], mode='lines', name='Forecast', line=dict(dash='dash', color='orange')))
    
    # Confidence Interval
    fig.add_trace(go.Scatter(
        x=pd.concat([forecast_df['date'], forecast_df['date'][::-1]]),
        y=pd.concat([forecast_df['upper_bound'], forecast_df['lower_bound'][::-1]]),
        fill='toself',
        fillcolor='rgba(255, 165, 0, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence Interval'
    ))
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Forecast Data")
    st.dataframe(forecast_df[['date', 'forecast_price', 'lower_bound', 'upper_bound']])

# --- PAGE 3: RISK & SHOCKS ---
elif page == "Risk & Shocks":
    st.header("Risk Assessment & Shock Monitoring")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Risk Score")
        score = risk_info['risk_score']
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,
            title = {'text': "Market Risk Score"},
            gauge = {'axis': {'range': [0, 100]},
                     'bar': {'color': "darkblue"},
                     'steps': [
                         {'range': [0, 30], 'color': "lightgreen"},
                         {'range': [30, 70], 'color': "yellow"},
                         {'range': [70, 100], 'color': "red"}],
                     'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': score}}))
        st.plotly_chart(fig, use_container_width=True)
        st.info(f"Risk Level: **{risk_info['risk_level']}**")
        
    with col2:
        st.subheader("Detected Shocks")
        if shock_info['is_shock']:
            st.error(f"Shock Detected! Severity: {shock_info['severity']}")
            st.write(shock_info['details'])
        else:
            st.success("No abnormal shocks detected.")
            
        st.subheader("Risk Factors")
        for tag in risk_info['explanation_tags']:
            st.warning(tag)

# --- PAGE 4: COMPARE MARKETS ---
elif page == "Compare Markets":
    st.header("📊 Compare Markets")
    
    col1, col2 = st.columns(2)
    with col1:
        c1 = st.selectbox("Commodity 1", db_commodities, key="c1", index=0)
        m1 = st.selectbox("Mandi 1", db_mandis, key="m1", index=0)
        data1 = get_live_data(c1, m1)
        
    with col2:
        c2 = st.selectbox("Commodity 2", db_commodities, key="c2", index=1 if len(db_commodities) > 1 else 0)
        m2 = st.selectbox("Mandi 2", db_mandis, key="m2", index=1 if len(db_mandis) > 1 else 0)
        data2 = get_live_data(c2, m2)
    
    st.subheader("Price Comparison")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data1['date'], y=data1['price'], mode='lines', name=f"{c1} ({m1})"))
    fig.add_trace(go.Scatter(x=data2['date'], y=data2['price'], mode='lines', name=f"{c2} ({m2})"))
    st.plotly_chart(fig, use_container_width=True)

# --- PAGE 5: NEWS ---
elif page == "News & Insights":
    st.header("📰 Global Agri-News & Sentiment")
    
    news_df = get_news_feed() # Renamed to news_df to avoid conflict with 'news' variable in snippet
    if not news_df.empty:
        for index, row in news_df.iterrows():
            with st.expander(f"{row['title']} - {row['source']}"):
                st.write(f"**Published**: {row['date']}")
                st.write(f"**Sentiment**: {row['sentiment']}")
                st.markdown(f"[Read Full Story]({row['url']})")
    else:
        st.subheader("Latest News")
        st.dataframe(news_df) # This will show an empty dataframe if news_df is empty

# --- MODEL PERFORMANCE ---
elif page == "Model Performance":
    st.header("📊 Model Performance & Evaluation")
    
    # 1. Fetch Data
    data = get_live_data(selected_commodity, selected_mandi)
    
    if len(data) > 60:
        # 2. Split Data (Hide last 30 days)
        train_data = data.iloc[:-30]
        test_data = data.iloc[-30:]
        
        # 3. Generate ML Forecast (Simulating 'Past' Prediction)
        agent = ForecastAgent()
        forecast_df = agent.generate_forecasts(train_data, selected_commodity, selected_mandi)
        
        # Align dates for comparison
        # Forecast generates next 30 days from end of train, which matches test_data dates
        
        # 4. Generate Baseline Forecast (Simple Moving Average of last 7 days of train)
        last_7_avg = train_data['price'].tail(7).mean()
        baseline_preds = [last_7_avg] * 30
        
        # 5. Calculate Metrics
        from sklearn.metrics import mean_absolute_error, mean_squared_error
        
        ml_preds = forecast_df['forecast_price'].values
        actuals = test_data['price'].values
        
        # Ensure lengths match (forecast is fixed 30, test might be slightly diff if gaps)
        min_len = min(len(ml_preds), len(actuals))
        ml_preds = ml_preds[:min_len]
        actuals = actuals[:min_len]
        baseline_preds = baseline_preds[:min_len]
        
        mae_ml = mean_absolute_error(actuals, ml_preds)
        rmse_ml = np.sqrt(mean_squared_error(actuals, ml_preds))
        
        mae_base = mean_absolute_error(actuals, baseline_preds)
        rmse_base = np.sqrt(mean_squared_error(actuals, baseline_preds))
        
        # 6. Display Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("ML Model MAE", f"₹{mae_ml:.2f}", delta=f"{-(mae_ml-mae_base):.2f} vs Baseline", delta_color="inverse")
        c2.metric("ML Model RMSE", f"₹{rmse_ml:.2f}")
        c3.metric("Baseline MAE", f"₹{mae_base:.2f}")
        
        st.info(f"**Evaluation on Hidden Test Set**: The model was trained on data up to {train_data['date'].max().date()} and asked to predict the next 30 days. We then compared it to what actually happened.")
        
        # 7. Plot Comparison
        eval_df = pd.DataFrame({
            "Date": test_data['date'].values[:min_len],
            "Actual Price": actuals,
            "ML Forecast": ml_preds,
            "Baseline (Avg)": baseline_preds
        })
        eval_df.set_index("Date", inplace=True)
        
        st.line_chart(eval_df)
        
    else:
        st.warning("Not enough historical data to run a full 30-day backtest evaluation.")

# --- EXPLANATION & INSIGHTS ---
elif page == "Explanation & Insights":
    st.header("AI Explanation & Insights")
    
    st.markdown("### 🤖 Market Intelligence Report")
    st.markdown(explanation['explanation'])
    
    st.info(f"**Confidence**: {explanation['confidence']}")
    
    st.subheader("Recommended Next Steps")
    st.write(explanation['next_steps'])
