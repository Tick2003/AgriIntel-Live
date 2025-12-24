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
from app.utils import get_live_data, load_css

# Page Config
st.set_page_config(page_title="AgriIntel", layout="wide", page_icon="🌾")
st.markdown(load_css(), unsafe_allow_html=True)

# Title
st.title("🌾 Agricultural Market Intelligence System")
st.markdown("---")

# Sidebar
st.sidebar.header("Configuration")
selected_commodity = st.sidebar.selectbox("Select Commodity", ["Potato", "Onion", "Tomato"])
selected_mandi = st.sidebar.selectbox("Select Mandi", ["Agra", "Nasik", "Bengaluru"])

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
page = st.sidebar.radio("Navigate", ["Market Overview", "Price Forecast", "Risk & Shocks", "Explanation & Insights"])

# --- PAGE 1: MARKET OVERVIEW ---
if page == "Market Overview":
    st.header(f"Market Overview: {selected_commodity} in {selected_mandi}")
    
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

# --- PAGE 4: EXPLANATION ---
elif page == "Explanation & Insights":
    st.header("AI Explanation & Insights")
    
    st.markdown("### 🤖 Market Intelligence Report")
    st.markdown(explanation['explanation'])
    
    st.info(f"**Confidence**: {explanation['confidence']}")
    
    st.subheader("Recommended Next Steps")
    st.write(explanation['next_steps'])
