import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from datetime import datetime
import threading
from utils.logger import logger

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.data_health import DataHealthAgent
from agents.forecast_execution import ForecastingAgent
from agents.shock_monitoring import AnomalyDetectionEngine
from agents.risk_scoring import MarketRiskEngine
from agents.explanation_report import AIExplanationAgent
from agents.arbitrage_engine import ArbitrageAgent
from agents.intelligence_core import IntelligenceAgent
from agents.user_profile import UserProfileAgent
from agents.notification_service import NotificationService
from agents.auth_manager import AuthAgent

# New Modules
from cv.grading_model import GradingModel
from utils.graph_algo import MandiGraph, get_demo_graph
from agents.language_manager import LanguageManager
from agents.chatbot_engine import ChatbotEngine
from agents.optimization_engine import OptimizationEngine
from agents.business_engine import B2BMatcher, FintechEngine
from agents.decision_support import DecisionAgent
from app.utils import get_live_data, get_news_feed, get_weather_data, get_db_options
import database.db_manager as db_manager
from app.terminal_theme import (
    inject_terminal_css, BG_COLOR, PANEL_COLOR, BORDER_COLOR, 
    TEXT_PRIMARY, TEXT_SECONDARY, ACCENT_GREEN, ACCENT_AMBER, 
    ACCENT_RED, ACCENT_BLUE, TEXT_MUTED, DIVIDER_COLOR, get_status_color
)

# Page Config
st.set_page_config(page_title="AgriIntel.in Terminal", layout="wide", page_icon="📉", initial_sidebar_state="expanded")
st.logo("logo.png")
inject_terminal_css()

# --- BOOT-TIME CACHE CLEAR (Prevents Stale Data on Redeploy) ---
if 'boot_cache_cleared' not in st.session_state:
    st.cache_data.clear()
    st.session_state['boot_cache_cleared'] = True

# Load Lang Manager
lang_manager = LanguageManager()

# --- TOP NAVIGATION (SIMULATED NAVBAR) ---
st.markdown(f"""
    <div style='display: flex; align-items: center; justify-content: space-between; height: 60px; background-color: {BG_COLOR}; border-bottom: 1px solid {BORDER_COLOR}; margin-bottom: 24px; padding: 0 24px;'>
        <div style='font-size: 20px; font-weight: 600; color: {TEXT_PRIMARY};'>AgriIntel.in <span style='color: {ACCENT_BLUE}; font-size: 14px;'>v2.0</span></div>
        <div style='color: {TEXT_SECONDARY}; font-size: 13px;'>{datetime.now().strftime('%d %b %Y | %H:%M:%S')}</div>
    </div>
""", unsafe_allow_html=True)


# --- INITIALIZE APP ---
if 'db_initialized' not in st.session_state:
    db_manager.init_db()
    st.session_state['db_initialized'] = True

# --- AUTHENTICATION GATEKEEPER ---
auth_agent = AuthAgent()

if not auth_agent.check_session():
    auth_agent.login_page()
    st.stop() 

# User is logged in
user_details = auth_agent.get_user_details()
user_email = user_details.get('email')
user_role = user_details.get('role', 'Viewer')
org_id = user_details.get('org_id')

# Get Org Name
org_name = "Unknown Org"
if org_id:
    org = db_manager.get_org_details(org_id)
    if org: org_name = org['name']

st.sidebar.image("logo.png", use_container_width=True)
st.sidebar.title("📉 Terminal Config")
st.sidebar.success(f"👤 {user_email}\n🏢 {org_name} ({user_role})")
auth_agent.logout_button()

# Sidebar
st.sidebar.header("Configuration")

LOCK_FILE = ".update.lock"

# Debug / Manual Update
if st.sidebar.button("🔄 Force Data Update"):
    if not os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "w") as f: f.write(str(datetime.now()))
            import etl.data_loader
            def manual_background_update():
                try:
                    etl.data_loader.run_daily_update(skip_swarm=False)
                    db_manager.set_last_update()
                except Exception as e:
                    logger.error(f"Manual Update Failed: {e}", exc_info=True)
                finally:
                    if os.path.exists(LOCK_FILE):
                        os.remove(LOCK_FILE)

            threading.Thread(target=manual_background_update, daemon=True).start()
            st.sidebar.success("Update triggered in background!")
            st.cache_data.clear() # Clear cache so fresh data is fetched after update
        except Exception as e:
            if os.path.exists(LOCK_FILE): os.remove(LOCK_FILE)
            st.sidebar.error(f"Manual trigger failed: {e}")
    else:
        st.sidebar.warning("Update already in progress...")

last_db_update = db_manager.get_last_update()
if last_db_update:
    st.sidebar.caption(f"DB Last Updated: {last_db_update}")
else:
    st.sidebar.caption("DB Update Status: Unknown")

# Dynamic options from DB
db_commodities, db_mandis = get_db_options()

selected_commodity = st.sidebar.selectbox("Select Commodity", db_commodities, index=0)
selected_mandi = st.sidebar.selectbox("Select Mandi", db_mandis, index=0)

# --- AUTO-UPDATE LOGIC ---
# Check for staleness using the already-fetched last_db_update
should_update = False
if not last_db_update:
    should_update = True
else:
    try:
        dt = datetime.strptime(last_db_update, "%Y-%m-%d %H:%M:%S")
        if (datetime.now() - dt).total_seconds() > 6 * 3600:
            should_update = True
    except:
        should_update = True

if should_update and not os.path.exists(LOCK_FILE):
    def background_update():
        import etl.data_loader
        import database.db_manager as dbm
        try:
            with open(LOCK_FILE, "w") as f: f.write(str(datetime.now()))
            etl.data_loader.run_daily_update(skip_swarm=True)
            dbm.set_last_update()
            st.cache_data.clear()
        except Exception as e:
            logger.error(f"Background Update Error: {e}", exc_info=True)
        finally:
            if os.path.exists(LOCK_FILE): os.remove(LOCK_FILE)

    threading.Thread(target=background_update, daemon=True).start()
    st.sidebar.info("🚀 System initializing data in background.")

if os.path.exists(LOCK_FILE):
    st.sidebar.warning("⏳ Intelligence agents are active in background.")
# -------------------------

# Initialize Agents
@st.cache_resource
def load_agents():
    return {
        "profile": UserProfileAgent(user_id=user_email), # Personalized
        "decision": DecisionAgent(),
        "risk": MarketRiskEngine(),
        "forecast": ForecastingAgent(),
        "explain": AIExplanationAgent(),
        "intel": IntelligenceAgent(),
        "lang": LanguageManager(),
        "chat": ChatbotEngine(db_manager),
        "opt": OptimizationEngine(),
        "b2b": B2BMatcher(),
        "fintech": FintechEngine(),
        "health": DataHealthAgent(),
        "shock": AnomalyDetectionEngine(),
        "arbitrage": ArbitrageAgent(),
        "notify": NotificationService() 
    }

agents = load_agents()

# --- PERSONALIZATION UI ---
try:
    user_profile = agents["profile"].get_profile()
    with st.sidebar.expander("⚙️ Personalization"):
        p_risk = st.selectbox("Risk Tolerance", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(user_profile.get('risk_tolerance', 'Medium')))
        p_transport = st.number_input("Transport Cost (₹/Q)", value=float(user_profile.get('transport_cost', 0.0)))
        
        if st.button("Save Preferences"):
            agents["profile"].update_profile(risk_tolerance=p_risk, transport_cost=p_transport)
            st.sidebar.success("Saved!")
            st.rerun()
except Exception as e:
    st.sidebar.error(f"Profile Error: {e}")

# Notification Log (Sidebar)
if "alerts" in st.session_state and st.session_state["alerts"]:
    with st.sidebar.expander("🔔 Notification Log", expanded=True):
        for alert in st.session_state["alerts"][:5]:
            st.code(alert, language="text")

# Load Data
# Helper wrapper for caching
@st.cache_data(ttl=600)
def fetch_and_process_data(commodity, mandi, db_update_time):
    """Fetches live data with cache-busting based on DB update time."""
    return get_live_data(commodity, mandi)

@st.cache_data(ttl=600)
def run_forecasting_agent(data, commodity, mandi):
    # This trains a model, so it MUST be cached
    agent = ForecastingAgent()
    return agent.generate_forecasts(data, commodity, mandi)

@st.cache_data(ttl=600)
def run_shock_risk_agents(data, forecast_df, sentiment_score, arrival_anomaly, weather_risk):
    # shock_agent = AnomalyDetectionEngine() # Removed as agents dict is used
    # risk_agent = MarketRiskEngine() # Removed as agents dict is used
    
    shock_info = agents["shock"].detect_shocks(data, forecast_df)
    risk_info = agents["risk"].calculate_risk_score(
        shock_info, 
        forecast_df['forecast_price'].std(), 
        data['price'].pct_change().std(),
        sentiment_score,
        arrival_anomaly,
        weather_risk
    )
    
    return shock_info, risk_info

@st.cache_data(ttl=600)
def run_explanation_agent(commodity, risk_info, shock_info, forecast_df):
    explain_agent = AIExplanationAgent()
    return explain_agent.generate_explanation(commodity, risk_info, shock_info, forecast_df)

@st.cache_data(ttl=600)
def run_decision_agent(current_price, forecast_df, risk_dict, shock_dict):
    agent = DecisionAgent()
    return agent.get_signal(current_price, forecast_df, risk_dict, shock_dict)

@st.cache_data(ttl=600)
def fetch_arbitrage_snapshot(commodity, all_mandis):
    frames = []
    for m in all_mandis:
        df = get_live_data(commodity, m)
        if not df.empty:
             frames.append(df)
    
    if frames:
        return pd.concat(frames)
    return pd.DataFrame()

# Load Data
data = fetch_and_process_data(selected_commodity, selected_mandi, last_db_update)
last_date = data['date'].max().strftime('%Y-%m-%d')
st.caption(f"Data Source: Agmarknet (Pilot Mode) | Last Updated: {last_date}")

# Run Agents (Cached)
health_status = agents["health"].check_daily_completeness(data) 
forecast_df = run_forecasting_agent(data, selected_commodity, selected_mandi)

# --- Calulate Risk Inputs (Phase 4) ---
# 1. Sentiment Score
news_df = get_news_feed()
sentiment_score = 0
if not news_df.empty:
    # Simple aggregations: Positive=+1, Negative=-1
    sent_map = {"Positive": 1, "Negative": -1, "Neutral": 0}
    sentiment_score = news_df['sentiment'].map(sent_map).mean()
    if pd.isna(sentiment_score): sentiment_score = 0

# 2. Arrival Anomaly
arrival_anomaly = 0
if len(data) > 30:
    recent_arrival = data['arrival'].iloc[-1]
    avg_arrival = data['arrival'].iloc[-30:].mean()
    if avg_arrival > 0:
        arrival_anomaly = (recent_arrival - avg_arrival) / avg_arrival

# 3. Weather Risk
weather_risk = 0
w_df = get_weather_data()
if not w_df.empty:
    w = w_df.iloc[-1]
    # Simple mock logic: High Temp or High Rain = Risk
    if w['temperature'] > 40 or w['rainfall'] > 50:
        weather_risk = 1.0

shock_info, risk_info = run_shock_risk_agents(data, forecast_df, sentiment_score, arrival_anomaly, weather_risk) 

# Check Notifications (Real-time)
agents["notify"].check_triggers(shock_info, risk_info, selected_commodity, selected_mandi)

decision_signal = run_decision_agent(data['price'].iloc[-1], forecast_df, risk_info, shock_info)
explanation = run_explanation_agent(selected_commodity, risk_info, shock_info, forecast_df)

# --- SIGNAL LOGGING (Phase 3) ---
last_date_str = data['date'].iloc[-1].strftime("%Y-%m-%d")

# Robust Logging
try:
    db_manager.log_signal(last_date_str, selected_commodity, selected_mandi, decision_signal['signal'], data['price'].iloc[-1])
except Exception as e:
    logger.error(f"Logging Error: {e}", exc_info=True)

# Fetch Stats
signal_stats = {}
try:
    if hasattr(db_manager, 'get_signal_stats'):
        signal_stats = db_manager.get_signal_stats(selected_commodity, selected_mandi)
except Exception as e:
    logger.error(f"Stats Error: {e}", exc_info=True)
# -------------------------------

# Navigation
nav_options = ["Dashboard", "Real-Time Desk", "Forecast", "Risk", "Arbitrage", "Voice", "News", "Consultant"]

if user_role in ['Admin', 'Analyst']:
    nav_options += ["Quality Grading (CV)", "Logistics (Graph)", "Data Reliability"]

page = st.sidebar.radio("Command Center", nav_options)


# --- PAGE 1: DASHBOARD ---
if page == "Dashboard":
    st.markdown(f"<h1>{selected_commodity} | {selected_mandi}</h1>", unsafe_allow_html=True)
    
    # 4-Metric Top Row
    col1, col2, col3, col4 = st.columns(4)
    if not data.empty:
        current_price = data['price'].iloc[-1]
        prev_price = data['price'].iloc[-2] if len(data) >= 2 else current_price
        delta = current_price - prev_price
        col1.metric("Current Price", f"₹{current_price:,.0f}", f"{delta:+.2f}")
    
    if not forecast_df.empty:
        f_price = forecast_df['forecast_price'].iloc[-1]
        f_delta = f_price - current_price
        col2.metric("30-Day Forecast", f"₹{f_price:,.0f}", f"{f_delta:+.2f}")
    
    col3.metric("Risk Score", f"{risk_info['risk_score']}/100", f"{risk_info['risk_level']}")
    col4.metric("Market Regime", risk_info['regime'])
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    # Main Forecast Chart (Full Width)
    with st.container():
        st.subheader("Tactical Intelligence: Price Projection")
        fig = go.Figure()
        
        # Historical Trace
        fig.add_trace(go.Scatter(
            x=data['date'].iloc[-60:], y=data['price'].iloc[-60:], 
            mode='lines', name='Actual Price', 
            line=dict(color=TEXT_PRIMARY, width=1.5)
        ))
        
        # Forecast Trace
        if not forecast_df.empty:
            fig.add_trace(go.Scatter(
                x=forecast_df['date'], y=forecast_df['forecast_price'], 
                mode='lines', name='AI Projection', 
                line=dict(color=ACCENT_BLUE, width=2, dash='dot')
            ))
            # Confidence Band
            fig.add_trace(go.Scatter(
                x=pd.concat([forecast_df['date'], forecast_df['date'][::-1]]),
                y=pd.concat([forecast_df['upper_bound'], forecast_df['lower_bound'][::-1]]),
                fill='toself', fillcolor='rgba(59, 130, 246, 0.1)',
                line=dict(color='rgba(255,255,255,0)'), name='Confidence'
            ))
            
        fig.update_layout(template="agriintel_terminal", height=450, showlegend=True)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Bottom Row: Two Columns (Risk vs Arbitrage)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Risk Decomposition")
        if 'breakdown' in risk_info:
            bd = risk_info['breakdown']
            fig_pie = px.pie(
                names=list(bd.keys()), values=list(bd.values()), 
                hole=0.6, color_discrete_sequence=[ACCENT_BLUE, ACCENT_AMBER, "#4B5563"]
            )
            fig_pie.update_layout(template="agriintel_terminal", height=250, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with c2:
        st.subheader("Regional Arbitrage Scan")
        if hasattr(db_manager, 'get_state_level_aggregation'):
            state_df = db_manager.get_state_level_aggregation()
            if not state_df.empty:
                st.dataframe(state_df.head(5), use_container_width=True)

# --- PAGE 2: FORECAST ---
elif page == "Forecast":
    st.markdown("<h1>Strategic Forecasting: 30-Day Projection</h1>", unsafe_allow_html=True)
    
    # 1. Main Forecast Plot
    fig = go.Figure()
    
    # Historical Trace
    fig.add_trace(go.Scatter(
        x=data['date'].iloc[-30:], y=data['price'].iloc[-30:], 
        mode='lines', name='Historical', 
        line=dict(color=TEXT_MUTED, width=1.5)
    ))
    
    # AI Forecast Trace
    fig.add_trace(go.Scatter(
        x=forecast_df['date'], y=forecast_df['forecast_price'], 
        mode='lines', name='AI Forecast', 
        line=dict(color=ACCENT_BLUE, width=2, dash='dot')
    ))
    
    # Confidence Interval
    fig.add_trace(go.Scatter(
        x=pd.concat([forecast_df['date'], forecast_df['date'][::-1]]),
        y=pd.concat([forecast_df['upper_bound'], forecast_df['lower_bound'][::-1]]),
        fill='toself', fillcolor='rgba(59, 130, 246, 0.08)',
        line=dict(color='rgba(255,255,255,0)'), name='Confidence band'
    ))
    
    fig.update_layout(template="agriintel_terminal", height=400, showlegend=True)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # 2. Profit Analytics (NEW)
    st.markdown("---")
    st.subheader("💰 Profit Analytics")
    st.write("Calculate potential returns if you hold your stock.")
    
    with st.container():
        c1, c2 = st.columns([1, 2])
        with c1:
            qty = st.number_input("Quantity (Quintals)", min_value=1, value=10, step=1)
            current_val = data['price'].iloc[-1] * qty
            st.metric("Current Value", f"₹{current_val:,.2f}")
        
        with c2:
            # Run Analysis
            sim_df = agents["decision"].simulate_profit(data['price'].iloc[-1], forecast_df, qty)
            
            if not sim_df.empty:
                # Formatting for display
                display_df = sim_df.copy()
                
                # Robustness Check for Stale Cache/Columns
                if 'Expected P&L' in display_df.columns:
                    display_df.rename(columns={'Expected P&L': 'Expected Profit'}, inplace=True)
                if 'Risk Adjusted P&L' in display_df.columns:
                    display_df.rename(columns={'Risk Adjusted P&L': 'Risk (±)'}, inplace=True)
                    
                # Format Cols if they exist
                if 'Expected Profit' in display_df.columns:
                    display_df['Expected Profit'] = display_df['Expected Profit'].apply(lambda x: f"₹{x:,.2f}")
                if 'Risk (±)' in display_df.columns:
                    display_df['Risk (±)'] = display_df['Risk (±)'].apply(lambda x: f"₹{x:,.2f}")
                if 'Expected Price' in display_df.columns:
                    display_df['Expected Price'] = display_df['Expected Price'].apply(lambda x: f"₹{x:,.2f}")
                
                st.dataframe(display_df, use_container_width=True)
                
                # Simple Insight
                if 'Expected Profit' in sim_df.columns:
                    best_idx = sim_df['Expected Profit'].idxmax()
                    best_scenario = sim_df.loc[best_idx]
                    
                    # Handle backward compat for risk col
                    risk_val = best_scenario.get('Risk (±)', 0)
                    if 'Risk Adjusted P&L' in best_scenario: risk_val = 0 # Fallback
                    
                    if best_scenario['Expected Profit'] > 0:
                        st.success(f"💡 Best Opportunity: Sell in **{best_scenario['Horizon']}** for expected gain of **₹{best_scenario['Expected Profit']:.2f}** (±₹{risk_val:.0f})")
                    else:
                        st.error("📉 Forecast suggests prices may fall. Selling now might be best.")
            else:
                st.warning("Not enough forecast data to run analysis.")

    st.subheader("Detailed Forecast Data")
    st.dataframe(forecast_df[['date', 'forecast_price', 'lower_bound', 'upper_bound']])

# --- PAGE 3: RISK ---
elif page == "Risk":
    st.markdown("<h1>Risk Assessment & Shock Monitoring</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Market Risk Decomposition")
        score = risk_info['risk_score']
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,
            number = {'font': {'color': TEXT_PRIMARY, 'size': 36}},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': DIVIDER_COLOR},
                'bar': {'color': ACCENT_BLUE, 'thickness': 0.25},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 2,
                'bordercolor': "rgba(59,130,246,0.4)",
                'steps': [
                    {'range': [0, 30], 'color': "rgba(61, 220, 132, 0.2)"},
                    {'range': [30, 70], 'color': "rgba(255, 176, 32, 0.2)"},
                    {'range': [70, 100], 'color': "rgba(255, 77, 79, 0.2)"}]
            }))
        fig.update_layout(template="agriintel_terminal", height=300)
        st.plotly_chart(fig, use_container_width=True)
        st.info(f"Risk Level: **{risk_info['risk_level']}**")
        
        # Risk Decomposition Pie Chart
        st.subheader("Risk Drivers")
        if 'breakdown' in risk_info:
            bd = risk_info['breakdown']
            fig_pie = px.pie(
                names=list(bd.keys()), 
                values=list(bd.values()), 
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            fig_pie.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)
        
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

# --- PAGE 4: ARBITRAGE ---
elif page == "Arbitrage":
    st.markdown("<h1>Compare Markets & Arbitrage Analysis</h1>", unsafe_allow_html=True)
    
    # Performance Optimized Regional Scan
    st.markdown("<div class='terminal-panel'>", unsafe_allow_html=True)
    st.subheader(f"Strategy Scan: {selected_commodity} Regional Corridor")
    st.caption(f"Base Origin: {selected_mandi} | Scan Depth: Cluster A")
    
    with st.spinner("Executing tactical scan..."):
        # Fetch snapshot for scan
        scan_mandis = db_mandis[:12] if len(db_mandis) > 12 else db_mandis
        snapshot_df = fetch_arbitrage_snapshot(selected_commodity, scan_mandis)
        
        if not snapshot_df.empty:
            arb_res = agents['arbitrage'].find_opportunities(
                selected_commodity, selected_mandi, snapshot_df, shock_info, {}
            )
            
            if not arb_res.empty:
                # Use only columns that exist in the result
                available_cols = [c for c in arb_res.columns if c in ['Target Mandi', 'Net Profit/Qt', 'Distance (km)', 'Target Price', 'Current Price', 'Confidence']]
                
                # Institutional Styling
                fmt = {}
                if 'Net Profit/Qt' in available_cols:
                    fmt['Net Profit/Qt'] = '₹{:.0f}'
                if 'Target Price' in available_cols:
                    fmt['Target Price'] = '₹{:.0f}'
                if 'Current Price' in available_cols:
                    fmt['Current Price'] = '₹{:.0f}'
                
                styled = arb_res[available_cols].style.format(fmt)
                if 'Net Profit/Qt' in available_cols:
                    styled = styled.map(
                        lambda x: f"color: {ACCENT_GREEN}; font-weight: 600" if isinstance(x, (float, int)) and x > 500 else "",
                        subset=['Net Profit/Qt']
                    )
                st.dataframe(styled, use_container_width=True)
            else:
                st.info("No arbitrage signals above the risk-adjusted threshold detected.")
        else:
            st.warning("Cluster data temporarily unavailable for this corridor.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("⚔️ Head-to-Head Comparison")
    
    col1, col2 = st.columns(2)
    with col1:
        c1 = st.selectbox("Commodity 1", db_commodities, key="c1", index=0)
        m1 = st.selectbox("Mandi 1", db_mandis, key="m1", index=0)
        data1 = get_live_data(c1, m1)
        
    with col2:
        c2 = st.selectbox("Commodity 2", db_commodities, key="c2", index=1 if len(db_commodities) > 1 else 0)
        m2 = st.selectbox("Mandi 2", db_mandis, key="m2", index=1 if len(db_mandis) > 1 else 0)
        data2 = get_live_data(c2, m2)
    
    st.subheader("Price Comparison Matrix")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data1['date'], y=data1['price'], 
        mode='lines', name=f"{c1}", 
        line=dict(color=TEXT_PRIMARY, width=1.5)
    ))
    fig.add_trace(go.Scatter(
        x=data2['date'], y=data2['price'], 
        mode='lines', name=f"{c2}", 
        line=dict(color=ACCENT_BLUE, width=1.5, dash='dot')
    ))
    fig.update_layout(template="agriintel_terminal", hovermode="x unified", transition_duration=0)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# --- PAGE: NEWS (Intelligence Feed) ---
elif page == "News":
    st.markdown("<h1>Intelligence Feed: Global Agri-Sentiment</h1>", unsafe_allow_html=True)
    
    news_df = get_news_feed() 
    if not news_df.empty:
        for index, row in news_df.iterrows():
            st.markdown(f"""
                <div class='terminal-panel'>
                    <p style='color:{ACCENT_BLUE}; font-size:0.8rem; margin-bottom:5px;'>{row['date']} | {row['source']}</p>
                    <h3 style='margin-top:0;'>{row['title']}</h3>
                    <p style='color:{TEXT_SECONDARY};'>{row['sentiment']}</p>
                    <a href='{row['url']}' style='color:{ACCENT_GREEN}; text-decoration:none;'>Read Analysis →</a>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Searching for intelligence signals... (Feed Empty)")


# --- PAGE: CONSULTANT (Analytical Intelligence) ---
elif page == "Consultant":
    st.markdown("<h1>Analytical Intelligence: Strategic Consultant</h1>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='terminal-panel'>
            <h3 style='color:{ACCENT_BLUE};'>Market Intelligence Report</h3>
            <p>{explanation['explanation']}</p>
            <div style='border-top: 1px solid {BORDER_COLOR}; padding-top:10px; margin-top:10px;'>
                <p style='color:{TEXT_SECONDARY};'><b>Next Steps</b>: {explanation['next_steps']}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Tactical Chat: Strategic Advisory")
    
    # Restored Chat Interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        role_label = "USER" if message["role"] == "user" else "AGRIINTEL"
        st.markdown(f"**{role_label}**: `{message['content']}`")

    if prompt := st.chat_input("Query the Tactical Intelligence Stack..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Mock Context Data
        context_data = {
            "signal": decision_signal['signal'],
            "current_price": data['price'].iloc[-1],
            "commodity": selected_commodity,
            "mandi": selected_mandi,
            "risk_score": risk_info.get('risk_score', 0),
            "regime": risk_info.get('regime', 'Unknown')
        }
        response = agents['intel'].get_chat_response(prompt, context_data)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()



# --- PAGE: QUALITY GRADING (CV) ---
elif page == "Quality Grading (CV)":
    st.markdown("<h1>Structural Quality Analytics</h1>", unsafe_allow_html=True)
    st.write("Upload visual data for institutional grading (Grade A/B/C).")
    
    grader = GradingModel()
    
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        c1, c2 = st.columns(2)
        with c1:
            st.image(uploaded_file, caption="Uploaded Produce", use_column_width=True)
            
        with c2:
            with st.spinner("Analyzing quality..."):
                # Save temp file for the mock/real grader
                with open("temp_grading_img.jpg", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                result = grader.predict("temp_grading_img.jpg")
                
                # cleanup
                try:
                    os.remove("temp_grading_img.jpg")
                except: pass
                
            if result:
                grade = result['grade']
                color = "green" if grade == "Grade A" else "orange" if grade == "Grade B" else "red"
                
                st.markdown(f"### Grade: :{color}[{grade}]")
                st.metric("Confidence", f"{result['confidence']*100:.1f}%")
                st.info(f"**Details**: {result['details']}")
                
                if grade == "Grade A":
                    st.success("✨ Premium Quality! You can list this at a 10-15% premium price.")
                elif grade == "Grade C":
                    st.warning("⚠️ Low Grade. Recommended for processing/canning industries rather than direct retail.")
                    
# --- PAGE: LOGISTICS (GRAPH ALGO) ---
elif page == "Logistics (Graph)":
    st.markdown("<h1>Network Supply Optimization</h1>", unsafe_allow_html=True)
    st.write("Find the most profitable market to sell at, accounting for transport costs.")
    
    mg = get_demo_graph()
    
    with st.form("logistics_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            start_loc = st.selectbox("Starting Location", list(mg.graph.keys()))
        with c2:
            qty_tons = st.number_input("Quantity (Tons)", min_value=1.0, value=5.0, step=0.5)
        with c3:
            # We use the selected commodity from global state or ask again
            comm = st.selectbox("Commodity", ["Onion", "Tomato", "Potato", "Rice"])
            
        submit = st.form_submit_button("Find Best Market")
        
    if submit:
        # 1. Fetch live prices for all destinations (Operational Data)
        # In real app, we'd query DB for all Mandis. Here we generate variation for demo.
        prices = {}
        base_price = 2500  # Rs/Quintal
        import random
        for mandi in mg.graph.keys():
            # Incorporate variability for regional analysis
            prices[mandi] = base_price + random.randint(-400, 600)
            
        # 2. Run Algo
        best, all_options = mg.find_best_profit_route(start_loc, qty_tons, prices)
        
        if best:
            st.subheader(f"🏆 Best Destination: {best['mandi']}")
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Net Profit", f"₹{best['net_profit']:,.0f}")
            m2.metric("Distance", f"{best['distance_km']} km")
            m3.metric("Selling Price", f"₹{best['price_per_q']}/q")
            
            st.success(f"**Recommendation**: Drive **{best['distance_km']} km** to **{best['mandi']}**. You will earn **₹{best['net_profit']:,.0f}** after paying **₹{best['transport_cost']:,.0f}** in fuel/transport.")
            
            st.markdown("### 📊 Comparison Table")
            df_logistics = pd.DataFrame(all_options)
            st.dataframe(df_logistics[['mandi', 'distance_km', 'price_per_q', 'transport_cost', 'net_profit']].style.highlight_max(subset=['net_profit'], color='#90ee90'))
        else:
            st.error("No valid routes found.")

# --- PAGE: VOICE (PREMIUM) ---
elif page == "Voice":
    st.markdown("<h1 style='text-align:center;'>Strategic Voice Gateway</h1>", unsafe_allow_html=True)
    st.markdown("<div style='height: 60px;'></div>", unsafe_allow_html=True)
    
    # Pulse Orb Container
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown("<div class='voice-orb'></div>", unsafe_allow_html=True)
        
        # State Indicators
        if "voice_state" not in st.session_state: st.session_state.voice_state = "Idle"
        
        state_colors = {"Idle": TEXT_MUTED, "Listening": ACCENT_GREEN, "Processing": ACCENT_BLUE, "Responding": ACCENT_AMBER}
        current_state = st.session_state.voice_state
        
        st.markdown(f"<p style='text-align:center; color:{state_colors.get(current_state)}; font-weight:500; font-size:18px;'>{current_state}...</p>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 1, 1])
        if c2.button("🎤 ACTIVATE", use_container_width=True):
            if st.session_state.voice_state == "Idle":
                st.session_state.voice_state = "Listening"
            else:
                st.session_state.voice_state = "Idle"
            st.rerun()
            
        if st.session_state.voice_state == "Listening":
            st.info("**Live Transcript**: 'AgriIntel, what is the arbitrage opportunity for Tomato today?'")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.subheader("Tactical Dialogue: Operational Logs")
    
    # Clean Transcript Log
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    for chat in reversed(st.session_state.chat_history):
        role_label = "USER" if chat['role'] == 'user' else "AGRIINTEL"
        st.markdown(f"**{role_label}**: `{chat['msg']}`")



# --- PAGE: DATA RELIABILITY (New Phase 6) ---
elif page == "Data Reliability":
    st.header("🛠️ Data Reliability Dashboard")

    st.caption("Monitor the health of the data ingestion pipeline and scraper performance.")
    
    # 1. Scraper Stats
    stats_df, success_rate = db_manager.get_scraper_stats()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Scraper Success Rate", f"{success_rate:.1f}%")
    if not stats_df.empty:
        avg_time = stats_df['duration_seconds'].mean()
        col2.metric("Avg Execution Time", f"{avg_time:.1f}s")
        last_run = stats_df.iloc[0]['timestamp']
        col3.metric("Last Run", last_run)
    else:
        col2.metric("Avg Execution Time", "N/A")
        col3.metric("Last Run", "N/A")

    st.subheader("Recent Execution Logs")
    st.dataframe(stats_df, use_container_width=True)
    
    st.markdown("---")
    
    # 2. Quality Alerts
    st.subheader("🚨 Data Quality Alerts")
    alerts_df = db_manager.get_recent_quality_alerts()
    
    if not alerts_df.empty:
        # Color code severity
        def highlight_severity(val):
            color = 'red' if val == 'CRITICAL' else 'orange' if val == 'WARNING' else 'black'
            return f'color: {color}'
            
        st.dataframe(alerts_df.style.map(highlight_severity, subset=['severity']), use_container_width=True)
    else:
        st.success("✅ No recent data quality issues detected.")
    
    # 3. Manual Trigger
    st.markdown("---")
    st.subheader("⚙️ Pipeline Control")
    if st.button("Run Manual Data Update (Admin)"):
        with st.spinner("Running ETL Pipeline..."):
            import contextlib
            import io
            f = io.StringIO()
            import etl.data_loader
            with contextlib.redirect_stdout(f):
                etl.data_loader.run_daily_update()
            
            output = f.getvalue()
            st.code(output)
            st.success("Manual Update Complete!")
            st.rerun()


# --- PAGE: REAL-TIME DESK ---
elif page == "Real-Time Desk":
    from app.utils import get_intraday_data, get_order_book_data, get_intraday_price_series
    import time as _time

    st.markdown("<h1>Real-Time Trading Desk</h1>", unsafe_allow_html=True)

    # --- Start the background stream generator (singleton) ---
    if 'stream_started' not in st.session_state:
        try:
            from etl.realtime_stream import start_realtime_generator
            start_realtime_generator(selected_commodity, selected_mandi)
            st.session_state['stream_started'] = True
        except Exception as e:
            st.warning(f"Stream generator unavailable: {e}")

    # --- Status Bar ---
    status_col1, status_col2, status_col3, status_col4 = st.columns(4)
    with status_col1:
        st.markdown(f"""
            <div style='display:flex; align-items:center; gap:8px;'>
                <div style='width:10px; height:10px; border-radius:50%;
                     background-color:{ACCENT_GREEN};
                     box-shadow: 0 0 8px {ACCENT_GREEN};
                     animation: pulse 2s infinite;'></div>
                <span style='color:{ACCENT_GREEN}; font-weight:600; font-size:14px;'>● LIVE</span>
            </div>
            <style>
                @keyframes pulse {{
                    0%, 100% {{ opacity: 1; }}
                    50% {{ opacity: 0.4; }}
                }}
            </style>
        """, unsafe_allow_html=True)
    with status_col2:
        st.caption(f"📍 {selected_commodity} | {selected_mandi}")
    with status_col3:
        st.caption(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
    with status_col4:
        if not data.empty:
            st.metric("Daily Modal", f"₹{data['price'].iloc[-1]:,.0f}")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # --- Row 1: Order Book + Transaction Feed ---
    col_book, col_feed = st.columns(2)

    with col_book:
        st.subheader("📊 Live Order Book")

        @st.fragment(run_every=3)
        def render_order_book():
            book = get_order_book_data(selected_commodity, selected_mandi, depth=8)
            bids = book.get("bids", pd.DataFrame())
            asks = book.get("asks", pd.DataFrame())

            if not bids.empty or not asks.empty:
                bc1, bc2 = st.columns(2)
                with bc1:
                    st.markdown(f"<p style='color:{ACCENT_GREEN}; font-weight:700; margin-bottom:4px;'>BID (Buy)</p>", unsafe_allow_html=True)
                    if not bids.empty:
                        for _, row in bids.head(8).iterrows():
                            pct_fill = min(100, row['quantity'] / 50 * 100)
                            st.markdown(f"""
                                <div style='position:relative; padding:4px 8px; margin:2px 0; border-radius:4px; overflow:hidden;'>
                                    <div style='position:absolute; left:0; top:0; bottom:0; width:{pct_fill}%;
                                         background:rgba(16,185,129,0.15); border-radius:4px;'></div>
                                    <div style='position:relative; display:flex; justify-content:space-between;'>
                                        <span style='color:{ACCENT_GREEN}; font-weight:600;'>₹{row['price']:,.0f}</span>
                                        <span style='color:{TEXT_MUTED}; font-size:12px;'>{row['quantity']:.1f}q</span>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.caption("No bids yet...")

                with bc2:
                    st.markdown(f"<p style='color:{ACCENT_RED}; font-weight:700; margin-bottom:4px;'>ASK (Sell)</p>", unsafe_allow_html=True)
                    if not asks.empty:
                        for _, row in asks.head(8).iterrows():
                            pct_fill = min(100, row['quantity'] / 50 * 100)
                            st.markdown(f"""
                                <div style='position:relative; padding:4px 8px; margin:2px 0; border-radius:4px; overflow:hidden;'>
                                    <div style='position:absolute; right:0; top:0; bottom:0; width:{pct_fill}%;
                                         background:rgba(239,68,68,0.15); border-radius:4px;'></div>
                                    <div style='position:relative; display:flex; justify-content:space-between;'>
                                        <span style='color:{TEXT_MUTED}; font-size:12px;'>{row['quantity']:.1f}q</span>
                                        <span style='color:{ACCENT_RED}; font-weight:600;'>₹{row['price']:,.0f}</span>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.caption("No asks yet...")

                # Spread indicator
                if not bids.empty and not asks.empty:
                    spread = asks['price'].iloc[0] - bids['price'].iloc[0]
                    st.markdown(f"<p style='text-align:center; color:{ACCENT_BLUE}; font-size:12px; margin-top:8px;'>Spread: ₹{spread:,.0f}</p>", unsafe_allow_html=True)
            else:
                st.info("Order book loading... Stream is initialising.")

        render_order_book()

    with col_feed:
        st.subheader("⚡ Live Transaction Feed")

        @st.fragment(run_every=3)
        def render_trade_feed():
            trades_df = get_intraday_data(selected_commodity, selected_mandi, limit=15)
            if not trades_df.empty:
                for _, row in trades_df.iterrows():
                    t_type = row.get('trade_type', 'TRADE')
                    if t_type == 'BID':
                        icon = "🟢"
                        color = ACCENT_GREEN
                    elif t_type == 'ASK':
                        icon = "🔴"
                        color = ACCENT_RED
                    else:
                        icon = "⚪"
                        color = ACCENT_BLUE

                    ts = str(row.get('timestamp', ''))[-12:]  # HH:MM:SS.mmm
                    st.markdown(f"""
                        <div style='display:flex; justify-content:space-between; align-items:center;
                             padding:4px 8px; border-bottom:1px solid {BORDER_COLOR};'>
                            <span style='font-size:12px;'>{icon} <b style='color:{color};'>{t_type}</b></span>
                            <span style='color:{TEXT_PRIMARY}; font-weight:600;'>₹{row['price']:,.0f}</span>
                            <span style='color:{TEXT_MUTED}; font-size:11px;'>{row['quantity']:.1f}q</span>
                            <span style='color:{TEXT_MUTED}; font-size:10px;'>{ts}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Waiting for transactions... Stream is populating.")

        render_trade_feed()

    st.markdown("---")

    # --- Row 2: Intraday Chart + RACE Model Card ---
    col_chart, col_card = st.columns([3, 1])

    with col_chart:
        st.subheader("📈 Intraday Price Chart")

        @st.fragment(run_every=5)
        def render_intraday_chart():
            intraday_df = get_intraday_price_series(selected_commodity, selected_mandi, limit=80)

            fig = go.Figure()

            # Historical daily prices (last 30 days)
            if not data.empty:
                fig.add_trace(go.Scatter(
                    x=data['date'].iloc[-30:], y=data['price'].iloc[-30:],
                    mode='lines', name='Daily Historical',
                    line=dict(color=TEXT_MUTED, width=1.5),
                    opacity=0.6,
                ))

            # Forecast overlay
            if not forecast_df.empty:
                fig.add_trace(go.Scatter(
                    x=forecast_df['date'], y=forecast_df['forecast_price'],
                    mode='lines', name='RACE Forecast',
                    line=dict(color=ACCENT_BLUE, width=2, dash='dot'),
                ))

            # Intraday ticks
            if not intraday_df.empty:
                fig.add_trace(go.Scatter(
                    x=intraday_df['timestamp'], y=intraday_df['price'],
                    mode='lines+markers', name='Intraday Ticks',
                    line=dict(color=ACCENT_GREEN, width=2),
                    marker=dict(size=4, color=ACCENT_GREEN),
                ))

            fig.update_layout(
                template="agriintel_terminal",
                height=380,
                showlegend=True,
                xaxis_title="Time",
                yaxis_title="Price (₹/Quintal)",
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        render_intraday_chart()

    with col_card:
        st.subheader("🧠 RACE Model Card")

        # Display RACE metadata if available
        try:
            forecast_agent = agents.get("forecast") or ForecastingAgent()
            race_result = forecast_agent.get_last_result()
        except Exception:
            race_result = None

        if race_result:
            # Regime badge
            regime = race_result.regime.regime
            regime_colors = {"STABLE": ACCENT_GREEN, "VOLATILE": ACCENT_AMBER, "CRISIS": ACCENT_RED}
            r_color = regime_colors.get(regime, ACCENT_BLUE)
            st.markdown(f"""
                <div style='background:rgba(255,255,255,0.03); border:1px solid {r_color};
                     border-radius:8px; padding:12px; margin-bottom:12px; text-align:center;'>
                    <p style='color:{TEXT_MUTED}; font-size:11px; margin:0; text-transform:uppercase; letter-spacing:0.1em;'>Market Regime</p>
                    <p style='color:{r_color}; font-size:24px; font-weight:700; margin:4px 0;'>{regime}</p>
                    <p style='color:{TEXT_MUTED}; font-size:11px; margin:0;'>Confidence: {race_result.regime.confidence:.0%}</p>
                </div>
            """, unsafe_allow_html=True)

            # Model weights
            st.markdown(f"<p style='color:{TEXT_MUTED}; font-size:11px; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;'>Ensemble Weights</p>", unsafe_allow_html=True)
            for model_name, weight in race_result.model_weights.items():
                pct = weight * 100
                bar_color = ACCENT_BLUE if weight > 0.25 else TEXT_MUTED
                st.markdown(f"""
                    <div style='margin-bottom:6px;'>
                        <div style='display:flex; justify-content:space-between; font-size:12px;'>
                            <span style='color:{TEXT_SECONDARY};'>{model_name}</span>
                            <span style='color:{TEXT_PRIMARY}; font-weight:600;'>{pct:.1f}%</span>
                        </div>
                        <div style='background:rgba(255,255,255,0.05); border-radius:4px; height:6px; overflow:hidden;'>
                            <div style='background:{bar_color}; width:{pct}%; height:100%; border-radius:4px;
                                 transition: width 0.5s ease;'></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    with status_col2:
        st.caption(f"📍 {selected_commodity} | {selected_mandi}")
    with status_col3:
        st.caption(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
    with status_col4:
        if not data.empty:
            st.metric("Daily Modal", f"₹{data['price'].iloc[-1]:,.0f}")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # --- Row 1: Order Book + Transaction Feed ---
    col_book, col_feed = st.columns(2)

    with col_book:
        st.subheader("📊 Live Order Book")

        @st.fragment(run_every=3)
        def render_order_book():
            book = get_order_book_data(selected_commodity, selected_mandi, depth=8)
            bids = book.get("bids", pd.DataFrame())
            asks = book.get("asks", pd.DataFrame())

            if not bids.empty or not asks.empty:
                bc1, bc2 = st.columns(2)
                with bc1:
                    st.markdown(f"<p style='color:{ACCENT_GREEN}; font-weight:700; margin-bottom:4px;'>BID (Buy)</p>", unsafe_allow_html=True)
                    if not bids.empty:
                        for _, row in bids.head(8).iterrows():
                            pct_fill = min(100, row['quantity'] / 50 * 100)
                            st.markdown(f"""
                                <div style='position:relative; padding:4px 8px; margin:2px 0; border-radius:4px; overflow:hidden;'>
                                    <div style='position:absolute; left:0; top:0; bottom:0; width:{pct_fill}%;
                                         background:rgba(16,185,129,0.15); border-radius:4px;'></div>
                                    <div style='position:relative; display:flex; justify-content:space-between;'>
                                        <span style='color:{ACCENT_GREEN}; font-weight:600;'>₹{row['price']:,.0f}</span>
                                        <span style='color:{TEXT_MUTED}; font-size:12px;'>{row['quantity']:.1f}q</span>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.caption("No bids yet...")

                with bc2:
                    st.markdown(f"<p style='color:{ACCENT_RED}; font-weight:700; margin-bottom:4px;'>ASK (Sell)</p>", unsafe_allow_html=True)
                    if not asks.empty:
                        for _, row in asks.head(8).iterrows():
                            pct_fill = min(100, row['quantity'] / 50 * 100)
                            st.markdown(f"""
                                <div style='position:relative; padding:4px 8px; margin:2px 0; border-radius:4px; overflow:hidden;'>
                                    <div style='position:absolute; right:0; top:0; bottom:0; width:{pct_fill}%;
                                         background:rgba(239,68,68,0.15); border-radius:4px;'></div>
                                    <div style='position:relative; display:flex; justify-content:space-between;'>
                                        <span style='color:{TEXT_MUTED}; font-size:12px;'>{row['quantity']:.1f}q</span>
                                        <span style='color:{ACCENT_RED}; font-weight:600;'>₹{row['price']:,.0f}</span>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.caption("No asks yet...")

                # Spread indicator
                if not bids.empty and not asks.empty:
                    spread = asks['price'].iloc[0] - bids['price'].iloc[0]
                    st.markdown(f"<p style='text-align:center; color:{ACCENT_BLUE}; font-size:12px; margin-top:8px;'>Spread: ₹{spread:,.0f}</p>", unsafe_allow_html=True)
            else:
                st.info("Order book loading... Stream is initialising.")

        render_order_book()

    with col_feed:
        st.subheader("⚡ Live Transaction Feed")

        @st.fragment(run_every=3)
        def render_trade_feed():
            trades_df = get_intraday_data(selected_commodity, selected_mandi, limit=15)
            if not trades_df.empty:
                for _, row in trades_df.iterrows():
                    t_type = row.get('trade_type', 'TRADE')
                    if t_type == 'BID':
                        icon = "🟢"
                        color = ACCENT_GREEN
                    elif t_type == 'ASK':
                        icon = "🔴"
                        color = ACCENT_RED
                    else:
                        icon = "⚪"
                        color = ACCENT_BLUE

                    ts = str(row.get('timestamp', ''))[-12:]  # HH:MM:SS.mmm
                    st.markdown(f"""
                        <div style='display:flex; justify-content:space-between; align-items:center;
                             padding:4px 8px; border-bottom:1px solid {BORDER_COLOR};'>
                            <span style='font-size:12px;'>{icon} <b style='color:{color};'>{t_type}</b></span>
                            <span style='color:{TEXT_PRIMARY}; font-weight:600;'>₹{row['price']:,.0f}</span>
                            <span style='color:{TEXT_MUTED}; font-size:11px;'>{row['quantity']:.1f}q</span>
                            <span style='color:{TEXT_MUTED}; font-size:10px;'>{ts}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Waiting for transactions... Stream is populating.")

        render_trade_feed()

    st.markdown("---")

    # --- Row 2: Intraday Chart + RACE Model Card ---
    col_chart, col_card = st.columns([3, 1])

    with col_chart:
        st.subheader("📈 Intraday Price Chart")

        @st.fragment(run_every=5)
        def render_intraday_chart():
            intraday_df = get_intraday_price_series(selected_commodity, selected_mandi, limit=80)

            fig = go.Figure()

            # Historical daily prices (last 30 days)
            if not data.empty:
                fig.add_trace(go.Scatter(
                    x=data['date'].iloc[-30:], y=data['price'].iloc[-30:],
                    mode='lines', name='Daily Historical',
                    line=dict(color=TEXT_MUTED, width=1.5),
                    opacity=0.6,
                ))

            # Forecast overlay
            if not forecast_df.empty:
                fig.add_trace(go.Scatter(
                    x=forecast_df['date'], y=forecast_df['forecast_price'],
                    mode='lines', name='RACE Forecast',
                    line=dict(color=ACCENT_BLUE, width=2, dash='dot'),
                ))

            # Intraday ticks
            if not intraday_df.empty:
                fig.add_trace(go.Scatter(
                    x=intraday_df['timestamp'], y=intraday_df['price'],
                    mode='lines+markers', name='Intraday Ticks',
                    line=dict(color=ACCENT_GREEN, width=2),
                    marker=dict(size=4, color=ACCENT_GREEN),
                ))

            fig.update_layout(
                template="agriintel_terminal",
                height=380,
                showlegend=True,
                xaxis_title="Time",
                yaxis_title="Price (₹/Quintal)",
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key="intraday_price_plotly_chart")

        render_intraday_chart()

    with col_card:
        st.subheader("🧠 RACE Model Card")

        # Display RACE metadata if available
        try:
            forecast_agent = agents.get("forecast") or ForecastingAgent()
            race_result = forecast_agent.get_last_result()
        except Exception:
            race_result = None

        if race_result:
            # Regime badge
            regime = race_result.regime.regime
            regime_colors = {"STABLE": ACCENT_GREEN, "VOLATILE": ACCENT_AMBER, "CRISIS": ACCENT_RED}
            r_color = regime_colors.get(regime, ACCENT_BLUE)
            st.markdown(f"""
                <div style='background:rgba(255,255,255,0.03); border:1px solid {r_color};
                     border-radius:8px; padding:12px; margin-bottom:12px; text-align:center;'>
                    <p style='color:{TEXT_MUTED}; font-size:11px; margin:0; text-transform:uppercase; letter-spacing:0.1em;'>Market Regime</p>
                    <p style='color:{r_color}; font-size:24px; font-weight:700; margin:4px 0;'>{regime}</p>
                    <p style='color:{TEXT_MUTED}; font-size:11px; margin:0;'>Confidence: {race_result.regime.confidence:.0%}</p>
                </div>
            """, unsafe_allow_html=True)

            # Model weights
            st.markdown(f"<p style='color:{TEXT_MUTED}; font-size:11px; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;'>Ensemble Weights</p>", unsafe_allow_html=True)
            for model_name, weight in race_result.model_weights.items():
                pct = weight * 100
                bar_color = ACCENT_BLUE if weight > 0.25 else TEXT_MUTED
                st.markdown(f"""
                    <div style='margin-bottom:6px;'>
                        <div style='display:flex; justify-content:space-between; font-size:12px;'>
                            <span style='color:{TEXT_SECONDARY};'>{model_name}</span>
                            <span style='color:{TEXT_PRIMARY}; font-weight:600;'>{pct:.1f}%</span>
                        </div>
                        <div style='background:rgba(255,255,255,0.05); border-radius:4px; height:6px; overflow:hidden;'>
                            <div style='background:{bar_color}; width:{pct}%; height:100%; border-radius:4px;
                                 transition: width 0.5s ease;'></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            # Confidence score
            st.metric("Overall Confidence", f"{race_result.confidence_score:.0f}/100")
            st.caption(f"Version: {race_result.model_version}")
        else:
            st.info("RACE model card loads after forecast execution.")
            st.caption("Run a forecast to populate model metadata.")

    st.markdown("---")

    # --- Row 3: News Ticker + Shock Alerts ---
    col_news, col_alerts = st.columns(2)

    with col_news:
        st.subheader("📰 Live News Ticker")

        @st.fragment(run_every=30)
        def render_news_ticker():
            news = get_news_feed()
            if not news.empty:
                for _, row in news.head(5).iterrows():
                    sent = row.get('sentiment', 'Neutral')
                    sent_color = ACCENT_GREEN if sent == 'Positive' else ACCENT_RED if sent == 'Negative' else TEXT_MUTED
                    st.markdown(f"""
                        <div style='padding:8px 12px; border-left:3px solid {sent_color};
                             margin-bottom:8px; background:rgba(255,255,255,0.02); border-radius:0 8px 8px 0;'>
                            <p style='color:{TEXT_PRIMARY}; font-size:13px; margin:0 0 4px 0; font-weight:500;'>{row['title']}</p>
                            <div style='display:flex; gap:12px;'>
                                <span style='color:{sent_color}; font-size:11px; font-weight:600;'>{sent}</span>
                                <span style='color:{TEXT_MUTED}; font-size:11px;'>{row.get('source', '')}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("News feed loading...")

        render_news_ticker()

    with col_alerts:
        st.subheader("🚨 Real-Time Alerts")

        @st.fragment(run_every=5)
        def render_realtime_alerts():
            # Get latest intraday trades
            recent_ticks = get_intraday_data(selected_commodity, selected_mandi, limit=100)
            daily_modal_price = data['price'].iloc[-1] if not data.empty else 0.0
            
            # Detect intraday shocks
            rt_shock = agents["shock"].detect_intraday_shocks(recent_ticks, daily_modal_price)
            # Calculate real-time risk
            rt_risk = agents["risk"].calculate_realtime_risk(risk_info, rt_shock)

            # Display current shock/risk status
            if rt_shock.get('is_shock', False):
                severity = rt_shock.get('severity', 'Unknown')
                sev_color = ACCENT_RED if severity in ['High', 'Critical'] else ACCENT_AMBER
                st.markdown(f"""
                    <div style='background:rgba(239,68,68,0.1); border:1px solid {sev_color};
                         border-radius:8px; padding:16px; margin-bottom:12px;
                         animation: alertPulse 2s infinite;'>
                        <p style='color:{sev_color}; font-size:16px; font-weight:700; margin:0;'>
                            ⚠️ SHOCK DETECTED — {severity}
                        </p>
                        <p style='color:{TEXT_SECONDARY}; font-size:13px; margin:4px 0 0 0;'>
                            Deviation of {rt_shock.get('max_deviation_pct', 0.0)}% from daily modal price. Last shock tick: ₹{rt_shock['shocks'][-1]['price'] if rt_shock['shocks'] else 0:,.2f}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style='background:rgba(16,185,129,0.05); border:1px solid rgba(16,185,129,0.3);
                         border-radius:8px; padding:16px; margin-bottom:12px;'>
                        <p style='color:{ACCENT_GREEN}; font-size:14px; font-weight:600; margin:0;'>
                            ✅ All Systems Normal
                        </p>
                        <p style='color:{TEXT_MUTED}; font-size:12px; margin:4px 0 0 0;'>
                            No price shocks or anomalies detected.
                        </p>
                    </div>
                """, unsafe_allow_html=True)

            # Risk summary
            st.markdown(f"""
                <div style='background:rgba(255,255,255,0.02); border:1px solid {BORDER_COLOR};
                     border-radius:8px; padding:12px; margin-top:8px;'>
                    <p style='color:{TEXT_MUTED}; font-size:11px; text-transform:uppercase; letter-spacing:0.1em; margin:0 0 8px 0;'>Risk Summary</p>
                    <div style='display:flex; justify-content:space-between;'>
                        <div>
                            <p style='color:{TEXT_MUTED}; font-size:11px; margin:0;'>Score</p>
                            <p style='color:{TEXT_PRIMARY}; font-size:20px; font-weight:700; margin:0;'>{rt_risk['risk_score']}/100</p>
                        </div>
                        <div>
                            <p style='color:{TEXT_MUTED}; font-size:11px; margin:0;'>Level</p>
                            <p style='color:{get_status_color(rt_risk["risk_level"])}; font-size:20px; font-weight:700; margin:0;'>{rt_risk['risk_level']}</p>
                        </div>
                        <div>
                            <p style='color:{TEXT_MUTED}; font-size:11px; margin:0;'>Regime</p>
                            <p style='color:{TEXT_PRIMARY}; font-size:20px; font-weight:700; margin:0;'>{rt_risk.get('regime', 'N/A')}</p>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        render_realtime_alerts()
