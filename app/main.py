import streamlit as st
# Version 1.1 - Hotfix for dependencies (xgboost, streamlit-oauth)
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from datetime import datetime

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.data_health import DataHealthAgent
from agents.forecast_execution import ForecastingAgent
from agents.shock_monitoring import AnomalyDetectionEngine
from agents.risk_scoring import MarketRiskEngine
from agents.explanation_report import AIExplanationAgent
from agents.arbitrage_engine import ArbitrageAgent # Restored
from agents.intelligence_core import IntelligenceAgent
from agents.user_profile import UserProfileAgent
from agents.notification_service import NotificationService
from agents.auth_manager import AuthAgent # New

# New Modules
from cv.grading_model import GradingModel
from utils.graph_algo import MandiGraph, get_demo_graph
from agents.language_manager import LanguageManager
from agents.chatbot_engine import ChatbotEngine
from agents.optimization_engine import OptimizationEngine
from agents.business_engine import B2BMatcher, FintechEngine
from app.utils import get_live_data, load_css, get_news_feed, get_weather_data, get_db_options
import database.db_manager as db_manager
from app.voice_admin import show_voice_admin
from app.terminal_theme import (
    inject_terminal_css, BG_COLOR, PANEL_COLOR, BORDER_COLOR, 
    TEXT_PRIMARY, TEXT_SECONDARY, ACCENT_GREEN, ACCENT_AMBER, 
    ACCENT_RED, ACCENT_BLUE, get_status_color
)
import importlib 
import agents.decision_support
import agents.risk_scoring
# Force Reload to prevent Stale Module errors on Cloud
importlib.reload(agents.decision_support)
importlib.reload(agents.risk_scoring)
from agents.decision_support import DecisionAgent
from agents.risk_scoring import MarketRiskEngine

# Page Config
st.set_page_config(page_title="AgriIntel.in Terminal", layout="wide", page_icon="📉")
inject_terminal_css()

# --- LANGUAGE SELECTOR ---
col_lang, _ = st.sidebar.columns([10, 1]) # Place at top of sidebar
with col_lang:
    selected_lang = st.selectbox("🌐 Language / भाषा / ଭାଷା", ["English", "Hindi", "Odia"])

# Load Lang Manager (Temp Access before full init just to translate title if needed, 
# but usually we init agents later. Let's do a quick inline init for title or wait).
# Better to init agents first. 
# Re-ordering main.py slightly to init agents earlier is complex.
# We will use the 'agents' dict later. For now, let's just proceed and using dynamic text.

# Terminal Header
st.title("AgriIntel.in | Tactical Intelligence Terminal")
st.markdown(f"<p style='color:#A0A6AD; margin-top:-20px;'>Operational Market Intelligence • National Unified Stack • {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>", unsafe_allow_html=True)

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

st.sidebar.success(f"👤 {user_email}\n🏢 {org_name} ({user_role})")
auth_agent.logout_button()

# Sidebar
st.sidebar.header("Configuration")

# Debug / Manual Update
if st.sidebar.button("🔄 Force Data Update"):
    with st.spinner("Forcing data update..."):
        import etl.data_loader
        importlib.reload(etl.data_loader)
        importlib.reload(db_manager)
        etl.data_loader.run_daily_update()
        db_manager.set_last_update()
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("Update Complete!")
        st.rerun()

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
from datetime import datetime
import etl.data_loader
import database.db_manager as db_manager

# Ensure DB is initialized and migrated
try:
    db_manager.init_db()
except Exception as e:
    print(f"DB Init failed: {e}")

try:
    if hasattr(db_manager, 'get_last_update'):
        last_update_str = db_manager.get_last_update()
    else:
        # Fallback if function is missing (e.g. old cached version)
        print("Warning: get_last_update not found in db_manager")
        last_update_str = None
except Exception as e:
    print(f"Auto-update check failed: {e}")
    last_update_str = None
should_update = False

if not last_update_str:
    should_update = True
else:
    last_update = datetime.strptime(last_update_str, "%Y-%m-%d %H:%M:%S")
    if (datetime.now() - last_update).total_seconds() > 6 * 3600:
        should_update = True
    
    # Check for Sparse Data (e.g. only 1 row) -> Force Update to Seed History
    try:
        # Quick check on a default commodity
        test_df = db_manager.get_latest_prices("Potato")
        if not test_df.empty and len(test_df) < 5:
            should_update = True
            print("Force updating due to sparse data...")
    except:
        pass

if should_update:
    import time
    try:
        # Progress UI
        st.info("🚀 New data available! Updating market intelligence...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(p, text):
            # Ensure p is float between 0.0 and 1.0
            p = min(max(float(p), 0.0), 1.0)
            progress_bar.progress(p)
            status_text.markdown(f"**{text}**")
            
        # Hot-fix: Force reload module to prevent Stale Module Error on Streamlit Cloud
        import importlib
        import database.db_manager as db_manager
        import etl.data_loader
        importlib.reload(db_manager)
        importlib.reload(etl.data_loader)
        
        etl.data_loader.run_daily_update(progress_callback=update_progress)
        
        status_text.success("✅ Update Complete!")
        time.sleep(1)
        st.cache_resource.clear()
        st.rerun()
    except Exception as e:
        import traceback
        st.error(f"Auto-update failed: {e}")
        st.code(traceback.format_exc())
        print(f"Update Error: {e}")
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
@st.cache_data(ttl=3600)
def fetch_and_process_data(commodity, mandi):
    return get_live_data(commodity, mandi)

@st.cache_data(ttl=3600)
def run_forecasting_agent(data, commodity, mandi):
    # This trains a model, so it MUST be cached
    agent = ForecastingAgent()
    return agent.generate_forecasts(data, commodity, mandi)

@st.cache_data(ttl=3600)
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

@st.cache_data(ttl=3600)
def run_explanation_agent(commodity, risk_info, shock_info, forecast_df):
    explain_agent = AIExplanationAgent()
    return explain_agent.generate_explanation(commodity, risk_info, shock_info, forecast_df)

@st.cache_data(ttl=3600)
def run_decision_agent(current_price, forecast_df, risk_dict, shock_dict):
    agent = DecisionAgent()
    return agent.get_signal(current_price, forecast_df, risk_dict, shock_dict)

@st.cache_data(ttl=3600)
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
data = fetch_and_process_data(selected_commodity, selected_mandi)
last_date = data['date'].max().strftime('%Y-%m-%d')
st.caption(f"Data Source: Agmarknet (Pilot Mode) | Last Updated: {last_date}")

# Run Agents (Cached)
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
    if hasattr(db_manager, 'log_signal'):
        db_manager.log_signal(last_date_str, selected_commodity, selected_mandi, decision_signal['signal'], data['price'].iloc[-1])
    else:
        # Hot-fix for stale module reload issue
        import importlib
        importlib.reload(db_manager)
        if hasattr(db_manager, 'log_signal'):
            db_manager.log_signal(last_date_str, selected_commodity, selected_mandi, decision_signal['signal'], data['price'].iloc[-1])
except Exception as e:
    print(f"Logging Error: {e}")

# Fetch Stats
signal_stats = {}
try:
    if hasattr(db_manager, 'get_signal_stats'):
        signal_stats = db_manager.get_signal_stats(selected_commodity, selected_mandi)
except Exception as e:
    print(f"Stats Error: {e}")
# -------------------------------

# Navigation
nav_options = [
    "AgriIntel (Dashboard)", "Forecast", "Risk", 
    "Arbitrage", "Voice", "News", "Consultant"
]

if user_role in ['Admin', 'Analyst']:
    # Keep advanced features at the bottom
    nav_options += ["Quality Grading (CV)", "Logistics (Graph)", "Data Reliability"]

page = st.sidebar.radio("Command Center", nav_options)


# --- PAGE 1: DASHBOARD ---
if page == "AgriIntel (Dashboard)":
    st.header(f"Market Overview: {selected_commodity} in {selected_mandi}")
    
    # Weather Widget
    weather_df = get_weather_data()
    if not weather_df.empty:
        w = weather_df.iloc[-1] 
        st.info(f"⛈️ **Weather Alert**: {w['condition']} | Temp: {w['temperature']}°C | Rainfall: {w['rainfall']}mm")
    
    # --- STRATEGY SIGNAL ---
    sig_color = decision_signal['color']
    sig_text = decision_signal.get('signal_text', decision_signal['signal']) 
    sig_reason = decision_signal['reason']
    st.markdown(f"""
        <div style="border-left: 4px solid {get_status_color(risk_info['risk_level'])}; padding-left: 15px; margin-bottom: 25px;">
            <p style="color: {TEXT_SECONDARY}; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 0;">Operational Strategy</p>
            <h2 style="margin: 0; color: {TEXT_PRIMARY};">{sig_text} | <span style="color: {get_status_color(risk_info['risk_level'])};">{risk_info['risk_level']} Risk</span></h2>
            <p style="color: {TEXT_SECONDARY}; margin-top: 5px;">{sig_reason}</p>
        </div>
    """, unsafe_allow_html=True)
    # ------------------------------

    col1, col2, col3, col4 = st.columns(4)
    if not data.empty:
        current_price = data['price'].iloc[-1]
        
        if len(data) >= 2:
            prev_price = data['price'].iloc[-2]
            delta = current_price - prev_price
        else:
            delta = 0.0

        col1.metric("Current Price", f"₹{current_price:,.0f}", f"{delta:+.2f}")
        
    # Forecast Metric (30d)
    if not forecast_df.empty:
        f_price = forecast_df['forecast_price'].iloc[-1]
        f_delta = f_price - current_price
        col2.metric("30-Day Forecast", f"₹{f_price:,.0f}", f"{f_delta:+.2f}")
    
    col3.metric("Risk Score", f"{risk_info['risk_score']}/100", f"{risk_info['risk_level']}")
    
    # Regime
    regime = risk_info['regime']
    col4.metric("Market Regime", regime)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Tactical Monitoring: Price Action")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['date'], y=data['price'], 
        mode='lines', name='Price', 
        line=dict(color='#E6E6E6', width=1.5)
    ))
    fig.update_layout(template="agriintel_terminal", hovermode="x unified", height=350)
    st.plotly_chart(fig, use_container_width=True)

# --- PAGE 2: FORECAST ---
elif page == "Forecast":
    st.header("Strategic Forecasting: 30-Day Projection")
    
    # 1. Plot
    fig = go.Figure()
    # Historical
    fig.add_trace(go.Scatter(
        x=data['date'].iloc[-30:], y=data['price'].iloc[-30:], 
        mode='lines', name='Historical', 
        line=dict(color='#666666', width=1)
    ))
    fig.add_trace(go.Scatter(x=forecast_df['date'], y=forecast_df['forecast_price'], mode='lines', name='Forecast', line_shape='spline', line=dict(dash='dash', color='#00C853', width=2)))
    fig.add_trace(go.Scatter(
        x=pd.concat([forecast_df['date'], forecast_df['date'][::-1]]),
        y=pd.concat([forecast_df['upper_bound'], forecast_df['lower_bound'][::-1]]),
        fill='toself',
        fillcolor='rgba(0, 200, 83, 0.15)', # Matches forecast green
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence Interval'
    ))
    fig.update_layout(template="agriintel_terminal", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    
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
    st.header("Risk Assessment & Shock Monitoring")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Market Risk Decomposition")
        score = risk_info['risk_score']
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,
            number = {'font': {'color': TEXT_PRIMARY, 'size': 36}},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': BORDER_COLOR},
                'bar': {'color': "#3B82F6", 'thickness': 0.2},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 0,
                'steps': [
                    {'range': [0, 30], 'color': "#064E3B"},
                    {'range': [30, 70], 'color': "#78350F"},
                    {'range': [70, 100], 'color': "#7F1D1D"}],
                'threshold': {'line': {'color': TEXT_PRIMARY, 'width': 2}, 'thickness': 0.75, 'value': score}}))
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
    st.header("📊 Compare Markets & Arbitrage")
    
    # 1. Arbitrage Analysis (NEW)
    st.subheader("🚛 Regional Arbitrage Opportunities")
    st.caption(f"Finding profit opportunities for **{selected_commodity}** starting from **{selected_mandi}**")
    
    with st.expander("🛠️ logistics Cost Configuration", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        in_fuel = c1.number_input("Fuel (₹/km/Qt)", value=0.02, format="%.3f")
        in_toll = c2.number_input("Toll (₹/Trip)", value=200)
        in_labor = c3.number_input("Labor (₹/Qt)", value=100)
        in_spoil = c4.number_input("Spoilage (%)", value=0.05, format="%.2f")
        
        cost_cfg = {
            "fuel_rate": in_fuel, 
            "toll": in_toll, 
            "labor": in_labor, 
            "spoilage": in_spoil
        }
    
    with st.spinner("Scanning regional markets..."):
        # Fetch data for current commodity across ALL mandis
        # We limit to first 10 mandis for demo speed if list is long
        scan_mandis = db_mandis[:10] if len(db_mandis) > 10 else db_mandis
        
        snapshot_df = fetch_arbitrage_snapshot(selected_commodity, scan_mandis)
        
        if not snapshot_df.empty:
            try:
                arb_df = agents['arbitrage'].find_opportunities(selected_commodity, selected_mandi, snapshot_df, shock_info, cost_cfg)
            except TypeError:
                # Handle Stale Cache: Old find_opportunities signature call failed
                # Reload module and re-instantiate
                import importlib
                import agents.arbitrage_engine
                importlib.reload(agents.arbitrage_engine)
                from agents.arbitrage_engine import ArbitrageAgent
                
                # Re-run with new agent
                temp_agent = ArbitrageAgent()
                arb_df = temp_agent.find_opportunities(selected_commodity, selected_mandi, snapshot_df, shock_info, cost_cfg)
            
            if not arb_df.empty:
                st.success(f"Execution Ready: {len(arb_df)} Arbitrage Opportunities Detected")
                # Format for display
                disp_cols = ['Target Mandi', 'Distance (km)', 'Net Profit/Qt', 'Profit (Bear Case)', 'Confidence']
                st.dataframe(arb_df[disp_cols].style.format({
                    'Net Profit/Qt': '₹{:.2f}',
                    'Profit (Bear Case)': '₹{:.2f}',
                    'Distance (km)': '{:.0f} km'
                }), use_container_width=True)
            else:
                if shock_info['is_shock']:
                    st.warning("⚠️ Market is currently undergoing a shock. Arbitrage scanning is disabled to prevent risky trades.")
                else:
                    st.info("No significant price gaps found (> ₹50 + transport) for this commodity.")
        else:
            st.warning("Insufficient regional data for arbitrage.")

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
    
    st.subheader("Price Comparison")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data1['date'], y=data1['price'], mode='lines+markers', name=f"{c1} ({m1})", line_shape='spline'))
    fig.add_trace(go.Scatter(x=data2['date'], y=data2['price'], mode='lines+markers', name=f"{c2} ({m2})", line_shape='spline'))
    fig.update_layout(template="agriintel_terminal", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# --- PAGE: NEWS (Intelligence Feed) ---
elif page == "News":
    st.header("Intelligence Feed: Global Agri-Sentiment")
    
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

# --- MODEL PERFORMANCE ---
elif page == "Model Performance":
    st.header("📊 Model Performance & Evaluation")
    
    # 1. Real-World Tracking (New Phase 7)
    st.subheader("📈 Real-World Accuracy Tracking")
    
    # Fetch Metrics History
    try:
        metrics_df = db_manager.get_performance_history(selected_commodity, selected_mandi)
        
        if not metrics_df.empty:
            latest = metrics_df.iloc[-1]
            
            # Health Score Gauge
            c1, c2, c3, c4 = st.columns(4)
            
            c1.metric("Model Health Score", f"{latest['health_score']:.1f}/100", 
                     delta=f"{latest['health_score'] - metrics_df.iloc[-2]['health_score']:.1f}" if len(metrics_df) > 1 else None)
            
            c2.metric("Current MAPE", f"{latest['mape']:.1f}%", inverse_mode=True)
            c3.metric("Current RMSE", f"₹{latest['rmse']:.1f}", inverse_mode=True)
            c4.metric("Samples Tracked", f"{latest['sample_size']}")
            
            # --- Drift Detection ---
            if latest['health_score'] < 60:
                 st.error(f"⚠️ MODEL DRIFT DETECTED: Health Score {latest['health_score']:.1f}/100 is critical. Retraining required.")
            elif latest['mape'] > 20: 
                 st.warning(f"⚠️ Accuracy Warning: MAPE {latest['mape']:.1f}% exceeds 20% threshold.")
            elif len(metrics_df) > 7:
                 avg_mape_7d = metrics_df.iloc[-8:-1]['mape'].mean()
                 if latest['mape'] > 1.5 * avg_mape_7d:
                      st.warning(f"⚠️ Drift Alert: Error spiked to {latest['mape']:.1f}% (vs 7-day avg {avg_mape_7d:.1f}%)")
            
            # Health Trend Chart
            st.caption("Model Health Trend (Last 90 Days)")
            st.line_chart(metrics_df.set_index('date')['health_score'])
            
            # Actual vs Predicted Chart (Historic)
            st.subheader("🔍 Forecast vs Actuals")
            track_df = db_manager.get_forecast_vs_actuals(selected_commodity, selected_mandi)
            
            if not track_df.empty:
                fig_perf = go.Figure()
                fig_perf.add_trace(go.Scatter(x=track_df['target_date'], y=track_df['actual_price'], name='Actual', line=dict(color='black', width=2)))
                fig_perf.add_trace(go.Scatter(x=track_df['target_date'], y=track_df['predicted_price'], name='Predicted', line=dict(color='green', dash='dot')))
                
                # Error Bars (optional, or just difference)
                fig_perf.update_layout(title="Prediction Accuracy Over Time", template="agriintel_terminal")
                st.plotly_chart(fig_perf, use_container_width=True)
                
        else:
            st.info("No tracking data available yet. Metrics will appear after the next daily update.")
            
    except Exception as e:
        st.error(f"Error loading metrics: {e}")

    st.markdown("---")
    st.subheader("🧪 Verification: Backtest Audit")
    
    if len(data) > 60:
        # 2. Split Data (Hide last 30 days)
        train_data = data.iloc[:-30]
        test_data = data.iloc[-30:]
        
        # 3. Generate ML Forecast (Historical Performance Mode)
        agent = ForecastingAgent()
        forecast_df = agent.generate_forecasts(train_data, selected_commodity, selected_mandi)
        
        # Align dates
        
        # 4. Generate Baseline Forecast (Naive Persistence: Last Known Price)
        last_price = train_data['price'].iloc[-1]
        baseline_preds = [last_price] * 30
        
        # 5. Calculate Metrics
        from sklearn.metrics import mean_absolute_error, mean_squared_error
        
        ml_preds = forecast_df['forecast_price'].values
        actuals = test_data['price'].values
        
        # Ensure lengths match
        min_len = min(len(ml_preds), len(actuals))
        ml_preds = ml_preds[:min_len]
        actuals = actuals[:min_len]
        baseline_preds = baseline_preds[:min_len]
        
        mae_ml = mean_absolute_error(actuals, ml_preds)
        mae_base = mean_absolute_error(actuals, baseline_preds)
        
        if mae_base > 0:
            improvement = ((mae_base - mae_ml) / mae_base) * 100
        else:
            improvement = 0
        
        # 6. Display Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("ML Accuracy Boost", f"{improvement:.1f}%", "vs Naive Baseline")
        c2.metric("ML Error (MAE)", f"₹{mae_ml:.2f}")
        c3.metric("Baseline Error", f"₹{mae_base:.2f}")
        
        st.info(f"**Evaluation on Hidden Test Set**: We hid the last 30 days of data and asked the AI to predict them. The chart below proves if the AI beat the market.")
        
        # 7. Plot Comparison (Smooth & Professional)
        dates_eval = test_data['date'].values[:min_len]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates_eval, y=actuals, mode='lines+markers', name='Actual Price (Truth)', line_shape='spline', line=dict(color='gray', width=3)))
        fig.add_trace(go.Scatter(x=dates_eval, y=ml_preds, mode='lines+markers', name='AI Forecast', line_shape='spline', line=dict(color='#00C853', width=3, dash='solid')))
        fig.add_trace(go.Scatter(x=dates_eval, y=baseline_preds, mode='lines+markers', name='Naive Baseline', line_shape='spline', line=dict(color='#FF5252', width=2, dash='dot')))
        
        fig.update_layout(template="agriintel_terminal", hovermode="x unified", title="Backtest Verification: AI vs Reality")
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("Not enough historical data to run a full 30-day backtest evaluation.")

# --- PAGE: CONSULTANT (Analytical Intelligence) ---
elif page == "Consultant":
    st.header("Analytical Intelligence: Strategic Consultant")
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
    st.header("Structural Quality Analytics (Phase II)")
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
    st.header("Network Supply Optimization")
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
    st.header("Strategic Voice Gateway")
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    
    # Pulse Orb Container
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown("<div class='voice-orb'></div>", unsafe_allow_html=True)
        
        # State Indicators
        if "listening" not in st.session_state: st.session_state.listening = False
        
        c1, c2, c3 = st.columns([1, 1, 1])
        if c2.button("🎤 ACTIVATE", use_container_width=True):
            st.session_state.listening = not st.session_state.listening
            
        if st.session_state.listening:
            st.markdown("<p style='text-align:center; color:#3DDC84; font-weight:bold;'>LISTENING...</p>", unsafe_allow_html=True)
            # Mock transcript
            st.info("**Transcript**: 'AgriIntel, what is the arbitrage opportunity for Tomato today?'")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.subheader("Operational Logs: Tactical Dialogue")
    
    # Display simplified transcript log
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    for chat in reversed(st.session_state.chat_history):
        color = "#E6E6E6" if chat['role'] == 'user' else "#3B82F6"
        role_label = "USER" if chat['role'] == 'user' else "AGRIINTEL"
        st.markdown(f"**{role_label}**: `{chat['msg']}`")

# --- PAGE: INSTITUTIONAL DASHBOARD ---
elif page == "Institutional Dashboard":
    st.header("🇮🇳 Institutional Market Dashboard")
    
    # 1. State-wise Aggregation
    state_df = db_manager.get_state_level_aggregation()
    
    if not state_df.empty:
        # Top Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("National Avg Price", f"₹{state_df['Avg Price'].mean():.0f}")
        c2.metric("Avg Market Volatility", f"{state_df['Volatility'].mean()*100:.1f}%")
        c3.metric("Active States Monitored", len(state_df))
        
        # Map Visualization
        st.subheader("📍 Real-Time Market Activity Map")
        coords = db_manager.get_mandi_coordinates()
        
        # Prepare Data for Map
        map_data = []
        for mandi, val in coords.items():
            map_data.append({"lat": val['lat'], "lon": val['lon'], "mandi": mandi, "state": val['state']})
            
        map_df = pd.DataFrame(map_data)
        
        # Advanced Map with Plotly
        fig = px.scatter_mapbox(
            map_df, lat="lat", lon="lon", hover_name="mandi", hover_data=["state"],
            zoom=3.5, height=500, size_max=15
        )
        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)

        # State Table
        st.subheader("📊 State-wise Performance")
        st.dataframe(state_df.style.format({
            "Avg Price": "₹{:.0f}",
            "Volatility": "{:.1%}"
        }), use_container_width=True)
    else:
        st.info("Insufficient data for national aggregation.")

# --- PAGE: DATA RELIABILITY (New Phase 6) ---
elif page == "Data Reliability":
    st.header("🛠️ Data Reliability Dashboard")
# ... (rest of the file)
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
            
        st.dataframe(alerts_df.style.applymap(highlight_severity, subset=['severity']), use_container_width=True)
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
            with contextlib.redirect_stdout(f):
                etl.data_loader.run_daily_update()
            
            output = f.getvalue()
            st.code(output)
            st.success("Manual Update Complete!")
            st.rerun()

