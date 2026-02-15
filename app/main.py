import streamlit as st
# Version 1.1 - Hotfix for dependencies (xgboost, streamlit-oauth)
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

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
import importlib 
import agents.decision_support
import agents.risk_scoring
# Force Reload to prevent Stale Module errors on Cloud
importlib.reload(agents.decision_support)
importlib.reload(agents.risk_scoring)
from agents.decision_support import DecisionAgent
from agents.risk_scoring import MarketRiskEngine

# Page Config
st.set_page_config(page_title="AgriIntel", layout="wide", page_icon="🌾")
st.markdown(load_css(), unsafe_allow_html=True)

# --- LANGUAGE SELECTOR ---
col_lang, _ = st.sidebar.columns([10, 1]) # Place at top of sidebar
with col_lang:
    selected_lang = st.selectbox("🌐 Language / भाषा / ଭାଷା", ["English", "Hindi", "Odia"])

# Load Lang Manager (Temp Access before full init just to translate title if needed, 
# but usually we init agents later. Let's do a quick inline init for title or wait).
# Better to init agents first. 
# Re-ordering main.py slightly to init agents earlier is complex.
# We will use the 'agents' dict later. For now, let's just proceed and using dynamic text.

st.title("🌾 AgriIntel / एग्री-इंटेल / ଆଗ୍ରି-ଇଣ୍ଟେଲ") 
st.markdown("---")

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
st.caption(f"Data Source: Agmarknet (Simulated) | Last Updated: {last_date}")

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
base_nav = [
    "Market Overview", "Price Forecast", "Risk & Shocks", 
    "Compare Markets", "News & Insights", "Explanation & Insights"
]
advanced_nav = [
    "Model Performance", "Quality Grading (CV)", "Logistics (Graph)", 
    "Advanced Planning", "B2B Marketplace", "Fintech Services", 
    "Developer API (SaaS)", "Institutional Dashboard", "WhatsApp Bot (Demo)", "AI Consultant", "Data Reliability"
]

if user_role in ['Admin', 'Analyst']:
    nav_options = base_nav + advanced_nav
else:
    nav_options = base_nav
    st.sidebar.info("🔒 Upgrade to Pro/Enterprise for Advanced Features")

page = st.sidebar.radio("Navigate", nav_options)


# --- PAGE 1: MARKET OVERVIEW ---
if page == "Market Overview":
    st.header(f"Market Overview: {selected_commodity} in {selected_mandi}")
    
    # Weather Widget
    weather_df = get_weather_data()
    if not weather_df.empty:
        w = weather_df.iloc[-1] 
        st.info(f"⛈️ **Weather Alert**: {w['condition']} | Temp: {w['temperature']}°C | Rainfall: {w['rainfall']}mm")
    
    # --- DECISION SIGNAL BANNER ---
    sig_color = decision_signal['color']
    # Use the confidence-rich text if available (Phase 4), else fallback
    sig_text = decision_signal.get('signal_text', decision_signal['signal']) 
    sig_reason = decision_signal['reason']
    
    # Calculate Reliability Label
    win_rate = signal_stats.get('win_rate', 0)
    total_signals = signal_stats.get('total', 0)
    
    reliability_badge = ""
    if total_signals > 5:
        if win_rate > 70: reliability_badge = "🏆 High Accuracy"
        elif win_rate > 50: reliability_badge = "✅ Reliable"
        else: reliability_badge = "⚠️ Low Confidence"
    else:
        reliability_badge = "🆕 Calibrating"

    st.markdown(f"""
    <div style="padding: 15px; border-radius: 10px; background-color: {'#e6fffa' if sig_color=='green' else '#fff5f5' if sig_color=='red' else '#fffaf0'}; border: 1px solid {sig_color}; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align_items: center;">
            <h3 style="color: {sig_color}; margin:0;">📢 Strategy: {sig_text}</h3>
            <span style="background-color: #fff; padding: 5px 10px; border-radius: 15px; border: 1px solid #ccc; font-size: 0.9em;">
                🎯 Accuracy: {win_rate:.0f}% ({reliability_badge})
            </span>
        </div>
        <p style="margin:5px 0 0 0;">{sig_reason}</p>
    </div>
    """, unsafe_allow_html=True)
    # ------------------------------

    col1, col2, col3 = st.columns(3)
    if not data.empty:
        current_price = data['price'].iloc[-1]
        
        if len(data) >= 2:
            prev_price = data['price'].iloc[-2]
            delta = current_price - prev_price
        else:
            prev_price = current_price
            delta = 0.0

        col1.metric("Current Price", f"₹{current_price:.2f}", f"{delta:.2f}")
        col2.metric("Daily Arrivals", f"{data['arrival'].iloc[-1]} tons")
    
    # Regime Badge Logic
    regime = risk_info['regime']
    regime_color = "green" if regime == "Stable" else "orange" if regime == "Volatile" else "red"
    col3.markdown(f"**Market Regime**")
    col3.markdown(f":{regime_color}[**{regime}**]")
    
    st.subheader("Historical Price Trend")
    # fig = px.line(data, x='date', y='price', title='Price History (90 Days)') # OLD
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['date'], y=data['price'], mode='lines+markers', name='Price', line_shape='spline', line=dict(color='#2962FF', width=2)))
    fig.update_layout(template="plotly_white", hovermode="x unified", title="Price History (90 Days)")
    st.plotly_chart(fig, use_container_width=True)

# --- PAGE 2: PRICE FORECAST ---
elif page == "Price Forecast":
    st.header("Price Forecast (Next 30 Days)")
    
    # 1. Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['date'], y=data['price'], mode='lines+markers', name='Historical', line_shape='spline', line=dict(color='gray')))
    fig.add_trace(go.Scatter(x=forecast_df['date'], y=forecast_df['forecast_price'], mode='lines', name='Forecast', line_shape='spline', line=dict(dash='dash', color='#00C853', width=2)))
    fig.add_trace(go.Scatter(
        x=pd.concat([forecast_df['date'], forecast_df['date'][::-1]]),
        y=pd.concat([forecast_df['upper_bound'], forecast_df['lower_bound'][::-1]]),
        fill='toself',
        fillcolor='rgba(0, 200, 83, 0.15)', # Matches forecast green
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence Interval'
    ))
    fig.update_layout(template="plotly_white", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    
    # 2. Profit Simulator (NEW)
    st.markdown("---")
    st.subheader("💰 Profit Simulator")
    st.write("Calculate potential returns if you hold your stock.")
    
    with st.container():
        c1, c2 = st.columns([1, 2])
        with c1:
            qty = st.number_input("Quantity (Quintals)", min_value=1, value=10, step=1)
            current_val = data['price'].iloc[-1] * qty
            st.metric("Current Value", f"₹{current_val:,.2f}")
        
        with c2:
            # Run Simulation
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
                st.warning("Not enough forecast data to run simulation.")

    st.subheader("Detailed Forecast Data")
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

# --- PAGE 4: COMPARE MARKETS ---
elif page == "Compare Markets":
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
                # Highlight best
                st.success(f"Found {len(arb_df)} opportunities (Margins > ₹50/Qt)!")
                
                # Format for display
                disp_cols = ['Target Mandi', 'Distance (km)', 'Net Profit/Qt', 'Profit (Bear Case)', 'Confidence', 'Action']
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
    fig.update_layout(template="plotly_white", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# --- PAGE 5: NEWS ---
elif page == "News & Insights":
    st.header("📰 Global Agri-News & Sentiment")
    
    news_df = get_news_feed() 
    if not news_df.empty:
        for index, row in news_df.iterrows():
            with st.expander(f"{row['title']} - {row['source']}"):
                st.write(f"**Published**: {row['date']}")
                st.write(f"**Sentiment**: {row['sentiment']}")
                st.markdown(f"[Read Full Story]({row['url']})")
    else:
        st.subheader("Latest News")
        st.dataframe(news_df)

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
                fig_perf.update_layout(title="Prediction Accuracy Over Time", template="plotly_white")
                st.plotly_chart(fig_perf, use_container_width=True)
                
        else:
            st.info("No tracking data available yet. Metrics will appear after the next daily update.")
            
    except Exception as e:
        st.error(f"Error loading metrics: {e}")

    st.markdown("---")
    st.subheader("🧪 Simulation: Backtest Verification")
    
    if len(data) > 60:
        # 2. Split Data (Hide last 30 days)
        train_data = data.iloc[:-30]
        test_data = data.iloc[-30:]
        
        # 3. Generate ML Forecast (Simulating 'Past' Prediction)
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
        
        fig.update_layout(template="plotly_white", hovermode="x unified", title="Backtest Verification: AI vs Reality")
        st.plotly_chart(fig, use_container_width=True)
        
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

# --- AI CONSULTANT (Phase 4) ---
elif page == "AI Consultant":
    st.header("🤖 AI Market Consultant")
    
    # Context for the Agent
    # Fetch sentiment summary
    latest_news = get_news_feed()
    if not latest_news.empty and 'sentiment_label' in latest_news.columns:
        sentiment_mode = latest_news['sentiment_label'].mode()[0]
    else:
        sentiment_mode = "Neutral"

    context_data = {
        "signal": decision_signal['signal'],
        "confidence": decision_signal.get('confidence', 50),
        "reason": decision_signal['reason'],
        "current_price": data['price'].iloc[-1],
        "commodity": selected_commodity,
        "mandi": selected_mandi,
        "risk_score": risk_info.get('risk_score', 0),
        "regime": risk_info.get('regime', 'Unknown'),
        "sentiment": sentiment_mode
    }

    # 1. Chat Interface
    st.markdown("ask me anything about the market, e.g., *'Should I sell?', 'What if it rains?', 'Forecast check'*")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Type your question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = agents['intel'].get_chat_response(prompt, context_data)
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

    # 2. Scenario Simulator (Sidebar)
    with st.sidebar:
        st.markdown("---")
        st.subheader("⚡ Scenario Simulator")
        st.caption("Test 'What-If' Events")
        
        sim_options = {
            "Heavy Rain": "heavy_rain",
            "Export Ban": "export_ban", 
            "Fuel Hike": "fuel_hike",
            "Festival": "festival_demand"
        }
        
        selected_sim = st.selectbox("Select Event", list(sim_options.keys()))
        
        if st.button("Simulate Impact"):
            sim_res = agents['intel'].run_scenario(context_data['current_price'], sim_options[selected_sim])
            if sim_res:
                st.sidebar.success(f"Price Change: {sim_res['change_pct']}")
                st.sidebar.metric("New Projected Price", f"₹{sim_res['new_price']:.2f}")
                st.sidebar.info(f"Reason: {sim_res['reason']}")

# --- PAGE: WHATSAPP BOT (ACCESSIBILITY) ---
elif page == "WhatsApp Bot (Demo)":
    st.header("💬 AgriBot (WhatsApp Mode)")
    st.caption("Simulating the SMS/WhatsApp experience for low-bandwidth users.")
    
    # Chat Interface
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
    # Input
    # Layout: Form for Text Input | Button for Voice
    c1, c2 = st.columns([4, 1])
    
    with c1:
        with st.form("chat_form", clear_on_submit=True):
            user_msg = st.text_input("Message", placeholder="e.g. Onion price in Cuttack?")
            sent = st.form_submit_button("Send 🚀")
            
    with c2:
        st.write("") 
        st.write("") 
        # Voice Trigger (Outside Form)
        mic_clicked = st.button("🎤 Voice") 
        
    if sent and user_msg:
        st.session_state.chat_history.append({"role": "user", "msg": user_msg})
        # Process
        resp = agents['chat'].process_query(user_msg)
        st.session_state.chat_history.append({"role": "bot", "msg": resp})
        
    if mic_clicked:
        st.info("🎤 Listening... (Simulated: 'Price of Tomato in Bhubaneswar')")
        # Mocking voice input processing
        mock_voice_text = "Price of Tomato in Bhubaneswar"
        st.session_state.chat_history.append({"role": "user", "msg": mock_voice_text})
        resp = agents['chat'].process_query(mock_voice_text)
        st.session_state.chat_history.append({"role": "bot", "msg": resp})
        resp = agents['chat'].process_query(mock_voice_text)
        st.session_state.chat_history.append({"role": "bot", "msg": resp})
        
    # Display History (Newest on top)
    for chat in reversed(st.session_state.chat_history):
        if chat['role'] == 'user':
            st.markdown(f"""
            <div style='background-color: #DCF8C6; padding: 10px; border-radius: 10px; margin: 5px; text-align: right; color: black;'>
                {chat['msg']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='background-color: #FFFFFF; padding: 10px; border-radius: 10px; margin: 5px; border: 1px solid #ddd; color: black;'>
                {chat['msg']}
            </div>
            """, unsafe_allow_html=True)

# --- PAGE: QUALITY GRADING (CV) ---
elif page == "Quality Grading (CV)":
    st.header("📸 AI Quality Grading")
    st.write("Upload a photo of your produce to get an instant standard grade (A, B, or C).")
    
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
    st.header("🚚 Smart Logistics Optimization")
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
        # 1. Fetch live prices for all destinations (Simulation/Real)
        # In real app, we'd query DB for all Mandis. Here we generate variation for demo.
        prices = {}
        base_price = 2500  # Rs/Quintal
        import random
        for mandi in mg.graph.keys():
            # Add random variation to simulate price differences
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

# --- PAGE: ADVANCED PLANNING (PHASE 3) ---
elif page == "Advanced Planning":
    st.header("🧠 Advanced Planning & Optimization")
    
    tab1, tab2 = st.tabs(["🌱 Crop Rotation (Next Season)", "🏭 Warehouse (Inventory)"])
    
    # --- TAB 1: CROP OPTIMIZATION ---
    with tab1:
        st.subheader("Profit Maximation Calculator")
        st.info("Uses Linear Programming to suggest the optimal area allocation for maximum profit.")
        
        c1, c2 = st.columns(2)
        with c1:
            total_land = st.number_input("Total Land Available (Acres)", 1.0, 100.0, 5.0)
        with c2:
            budget = st.number_input("Total Budget (₹)", 10000, 1000000, 50000, step=5000)
            
        if st.button("Generate Optimal Plan"):
            with st.spinner("Running Simplex Algorithm..."):
                res = agents['opt'].optimize_crop_mix(total_land, budget)
            
            if res['status'] == 'Failed':
                st.error(f"Optimization Failed: {res.get('message')}")
            else:
                st.success(f"Optimization Status: {res['status']}")
                
                # Metrics
                m1, m2, m3 = st.columns(3)
                m1.metric("Projected Profit", f"₹{res['total_profit']:,.0f}")
                m2.metric("Land Utilized", f"{res['used_land']} / {total_land} Acres")
                m3.metric("Capital Used", f"₹{res['used_budget']:,.0f}")
                
                # Chart
                alloc = res['allocations']
                if sum(alloc.values()) > 0:
                    df_alloc = pd.DataFrame(list(alloc.items()), columns=['Crop', 'Acres'])
                    fig = px.pie(df_alloc, values='Acres', names='Crop', title='Recommended Land Allocation')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Budget too low to plant available crops.")

    # --- TAB 2: INVENTORY OPTIMIZATION ---
    with tab2:
        st.subheader("Inventory Control (EOQ)")
        st.write("Determine the ideal order size to minimize holding and ordering costs.")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            annual_demand = st.number_input("Annual Demand (Units)", 100, 10000, 1000)
        with c2:
            order_cost = st.number_input("Ordering Cost per Order (₹)", 100, 5000, 500)
        with c3:
            hold_cost = st.number_input("Holding Cost per Unit/Year (₹)", 1, 500, 20)
            
        eoq = agents['opt'].calculate_eoq(annual_demand, order_cost, hold_cost)
        
        st.divider()
        st.metric("Economic Order Quantity (EOQ)", f"{eoq} Units")
        
        st.info(f"💡 You should order **{eoq} units** at a time to minimize total costs.")

# --- PAGE: B2B MARKETPLACE ---
elif page == "B2B Marketplace":
    st.header("🤝 B2B Matchmaking")
    st.caption("Connect directly with Millers, Retail Chains, and Exporters.")
    
    with st.expander("📝 Post a Sell Order", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            sell_crop = st.selectbox("Crop to Sell", ["Onion", "Tomato", "Potato", "Rice", "Wheat"])
        with c2:
            sell_qty = st.number_input("Quantity (Tons)", 1.0, 100.0, 5.0)
        with c3:
            sell_mandi = st.selectbox("Your Location", ["Nasik", "Cuttack", "Bhubaneswar", "Azadpur", "Kolkata"])
            
    if st.button("Find Buyers"):
        matches = agents['b2b'].find_buyers(sell_crop, sell_qty, sell_mandi)
        
        st.subheader(f"Found {len(matches)} Interested Buyers")
        for m in matches:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.markdown(f"**{m['buyer_name']}** ({m['type']})")
                    st.caption(f"📍 {m['location']} • {m['distance']} km away")
                with col2:
                    st.metric("Bid Price", f"₹{m['bid_price']}/q")
                with col3:
                    score_color = "green" if m['match_score'] > 80 else "orange"
                    st.markdown(f"Match: :{score_color}[**{m['match_score']}%**]")
                with col4:
                    st.button("Connect 📞", key=m['buyer_name'])
                st.divider()

# --- PAGE: FINTECH SERVICES ---
elif page == "Fintech Services":
    st.header("🏦 Agri-Fintech Hub")
    st.write("Get instant loans based on your crop yield history and reliability score.")
    
    # Mock History Data
    st.subheader("Your Farm Profile")
    yield_data = [4.5, 4.2, 4.8, 4.6, 4.7] # Tons/Acre for last 5 seasons
    reliability = 0.95 # High
    
    col1, col2 = st.columns(2)
    with col1:
        st.line_chart(yield_data)
        st.caption("Yield Stability (Last 5 Seasons)")
    with col2:
        offer = agents['fintech'].calculate_credit_score(yield_data, reliability)
        
        # Credit Card UI
        st.markdown(f"""
        <div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white;">
            <h3>Agri-Credit Score</h3>
            <h1 style="font-size: 48px; margin: 0;">{offer['credit_score']}</h1>
            <p>Rating: <strong>{offer['rating']}</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
    st.subheader("Loan Offers for You")
    c1, c2, c3 = st.columns(3)
    c1.metric("Max Loan Eligibility", f"₹{offer['max_loan']:,.0f}")
    c2.metric("Interest Rate", f"{offer['interest_rate']}% p.a.")
    c3.button("Apply Now 🚀")

# --- PAGE: DEVELOPER API ---
elif page == "Developer API (SaaS)":
    st.header("🔌 AgriIntel for Developers")
    st.write("Power your own apps with our market intelligence API.")
    
    st.markdown("### Pricing Plans")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("**Starter**\n\nFree\n\n100 req/day")
    with c2:
        st.success("**Pro**\n\n₹499/mo\n\n10,000 req/day")
    with c3:
        st.warning("**Enterprise**\n\nCustom\n\nUnlimited")
        
    st.divider()
    
    st.subheader("Your API Key")
    st.code("sk_live_51Ha7x...", language="bash")
    
    st.subheader("Documentation Example")
    st.code("""
# GET /api/v1/forecast?commodity=Onion&mandi=Nasik
import requests
res = requests.get("https://api.agriintel.in/v1/forecast")
print(res.json())
# Output: {"predicted_price": 2650, "trend": "Bullish"}
    """, language="python")


# --- PAGE: BACKTEST SIMULATOR (Phase 8) ---
elif page == "Backtest Simulator":
    st.header("⏪ Time Travel & Backtesting")
    st.caption("Test the AI's strategy against historical data (Simulation Mode).")
    
    from agents.backtesting_engine import BacktestEngine
    
    # Inputs
    c1, c2, c3 = st.columns(3)
    c1.info(f"**Commodity**: {selected_commodity}")
    c2.info(f"**Market**: {selected_mandi}")
    initial_cap = c3.number_input("Initial Capital (₹)", 10000, 10000000, 100000, step=10000)
    
    if st.button("Run Simulation 🏃‍♂️"):
        be = BacktestEngine(initial_capital=initial_cap)
        
        with st.spinner("Replaying market history..."):
            # Fetch last 365 days by default or max avail
            equity_df, metrics, trades_df = be.run_backtest(selected_commodity, selected_mandi)
            
        if metrics and "error" not in metrics:
            # Top Metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Return", f"{metrics['Total Return']:.1f}%", 
                      delta=f"{metrics['Total Return'] - metrics['Benchmark Return']:.1f}% vs Hold")
            m2.metric("Final Equity", f"₹{metrics['Final Equity']:,.0f}")
            m3.metric("Max Drawdown", f"{metrics['Max Drawdown']:.1f}%")
            m4.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")
            
            # Equity Curve
            st.subheader("Performance vs Buy & Hold")
            
            # Normalize for comparison
            equity_df['rel_strategy'] = (equity_df['strategy_equity'] / equity_df['strategy_equity'].iloc[0]) * 100
            equity_df['rel_benchmark'] = (equity_df['price'] / equity_df['price'].iloc[0]) * 100
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=equity_df['date'], y=equity_df['rel_strategy'], name='AI Strategy', line=dict(color='green', width=2)))
            fig.add_trace(go.Scatter(x=equity_df['date'], y=equity_df['rel_benchmark'], name='Buy & Hold', line=dict(color='gray', dash='dot')))
            fig.update_layout(title="Equity Curve (Rebased to 100)", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            
            # Trade Log
            with st.expander("🛠️ Debug Tools"):
                st.json(st.session_state)
            with st.expander("📜 Trade Log"):
                st.dataframe(trades_df.style.format({"price": "{:.2f}", "value": "{:,.0f}"}))
                
        else:
            st.error(f"Backtest Failed: {metrics.get('error') if metrics else 'Unknown Error'}")

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
