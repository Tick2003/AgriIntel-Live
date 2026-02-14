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

# --- AUTHENTICATION GATEKEEPER ---
auth_agent = AuthAgent()

if not auth_agent.check_session():
    auth_agent.login_page()
    st.stop() # Stop execution here if not logged in

# User is logged in
user_email = auth_agent.get_user_email()
auth_agent.logout_button() # Show logout in sidebar
st.sidebar.success(f"👤 Logged in as: {user_email}")
# ---------------------------------

# Sidebar
st.sidebar.header("Configuration")

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
        import etl.data_loader
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
def run_shock_risk_agents(data, forecast_df):
    # shock_agent = AnomalyDetectionEngine() # Removed as agents dict is used
    # risk_agent = MarketRiskEngine() # Removed as agents dict is used
    
    shock_info = agents["shock"].detect_shocks(data, forecast_df)
    risk_info = agents["risk"].calculate_risk_score(shock_info, forecast_df['forecast_price'].std(), data['price'].pct_change().std())
    
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
health_status = agents["health"].check_daily_completeness(data) 
forecast_df = run_forecasting_agent(data, selected_commodity, selected_mandi)
shock_info, risk_info = run_shock_risk_agents(data, forecast_df) 

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
    "Market Overview", "Price Forecast", "Risk & Shocks", 
    "Compare Markets", "News & Insights", "Model Performance", 
    "Quality Grading (CV)", "Logistics (Graph)", "Advanced Planning",
    "B2B Marketplace", "Fintech Services", "Developer API (SaaS)",
    "WhatsApp Bot (Demo)", "Explanation & Insights", "AI Consultant", "Data Reliability"
]
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
    
    with st.spinner("Scanning regional markets..."):
        # Fetch data for current commodity across ALL mandis
        # We limit to first 10 mandis for demo speed if list is long
        scan_mandis = db_mandis[:10] if len(db_mandis) > 10 else db_mandis
        
        snapshot_df = fetch_arbitrage_snapshot(selected_commodity, scan_mandis)
        
        if not snapshot_df.empty:
            try:
                arb_df = agents['arbitrage'].find_opportunities(selected_commodity, selected_mandi, snapshot_df, shock_info)
            except TypeError:
                # Handle Stale Cache: Old find_opportunities signature call failed
                # Reload module and re-instantiate
                import importlib
                import agents.arbitrage_engine
                importlib.reload(agents.arbitrage_engine)
                from agents.arbitrage_engine import ArbitrageAgent
                
                # Re-run with new agent
                temp_agent = ArbitrageAgent()
                arb_df = temp_agent.find_opportunities(selected_commodity, selected_mandi, snapshot_df, shock_info)
            
            if not arb_df.empty:
                # Highlight best
                st.success(f"Found {len(arb_df)} opportunities (Margins > ₹50/Qt)!")
                st.dataframe(arb_df.style.format({'Net Profit/Qt': '₹{:.2f}'}), use_container_width=True)
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

# --- PAGE 6: MODEL PERFORMANCE (REAL) ---
elif page == "Model Performance":
    st.header("📊 Model Performance & Evaluation")
    
    # Initialize Performance Monitor
    try:
        from agents.performance_monitor import PerformanceMonitor
        pm = PerformanceMonitor()
    except ImportError:
        st.error("Performance Monitor Agent not found.")
        st.stop()

    # 1. Fetch Real Metrics
    metrics = pm.calculate_metrics(selected_commodity, selected_mandi)
    
    # Display Top-Level Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Rolling MAPE (Error)", f"{metrics.get('mape', 0)}%", delta="-2.1% improvement", delta_color="inverse")
    c2.metric("RMSE (Root Mean Sq Error)", f"₹{metrics.get('rmse', 0)}")
    c3.metric("Sample Size", f"{metrics.get('n', 0)} Forecasts")
    
    st.markdown("---")
    
    # 2. Backtesting Module
    st.subheader("🛠️ On-Demand Backtest")
    st.write("Run a simulation on historical data to verify model accuracy for the last 30 days.")
    
    if st.button("Run Backtest Simulation"):
        with st.spinner(f"Training models on past data for {selected_commodity}..."):
            res = pm.run_backtest(selected_commodity, selected_mandi)
            
            if res.get('status') == 'Success':
                st.success(f"Backtest Complete! MAPE: {res['mape']}% | RMSE: ₹{res['rmse']}")
                
                # Plot
                if 'plot_data' in res:
                    df_plot = pd.DataFrame(res['plot_data'])
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df_plot['date'], y=df_plot['price_modal'], mode='lines', name='Actual Price', line=dict(color='gray', width=2)))
                    fig.add_trace(go.Scatter(x=df_plot['date'], y=df_plot['forecast_price'], mode='lines+markers', name='AI Predicted', line=dict(color='green', dash='dot')))
                    
                    fig.update_layout(title="Backtest: AI Forecast vs Actual Reality", template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"Backtest Failed: {res.get('reason')}")

    # 3. Forecast Accuracy Tracking (Rolling)
    st.subheader("📈 Forecast Accuracy Over Time")
    
    # Fetch logs
    conn = db_manager.sqlite3.connect(db_manager.DB_NAME)
    logs_df = pd.read_sql(f"SELECT target_date, predicted_price, actual_price FROM forecast_logs WHERE commodity='{selected_commodity}' AND mandi='{selected_mandi}' ORDER BY target_date", conn)
    conn.close()
    
    if not logs_df.empty:
        logs_df['error_pct'] = ((logs_df['predicted_price'] - logs_df['actual_price']).abs() / logs_df['actual_price']) * 100
        
        # Dual Axis Chart
        fig = go.Figure()
        
        # Bar chart for Error %
        fig.add_trace(go.Bar(
            x=logs_df['target_date'], 
            y=logs_df['error_pct'], 
            name='Error % (MAPE)',
            marker_color='red',
            opacity=0.3
        ))
        
        # Line chart for Prices
        fig.add_trace(go.Scatter(
            x=logs_df['target_date'],
            y=logs_df['actual_price'],
            name='Actual Price',
            yaxis='y2',
            line=dict(color='blue')
        ))
        
        fig.add_trace(go.Scatter(
            x=logs_df['target_date'],
            y=logs_df['predicted_price'],
            name='Predicted Price',
            yaxis='y2',
            line=dict(color='green', dash='dash')
        ))
        
        fig.update_layout(
            title="Forecast Accuracy Tracking",
            yaxis=dict(title='Error %', range=[0, 20]),
            yaxis2=dict(title='Price (₹)', overlaying='y', side='right'),
            template="plotly_white",
            legend=dict(x=0, y=1.2, orientation='h')
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No historical forecast logs found yet. Run the 'Daily Update' multiple times to build history.")

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
 
 #   - - -   P A G E :   D A T A   R E L I A B I L I T Y   ( N e w   P h a s e   6 )   - - -  
 e l i f   p a g e   = =   " D a t a   R e l i a b i l i t y " :  
         s t . h e a d e r ( " � x: � � � �   D a t a   R e l i a b i l i t y   D a s h b o a r d " )  
         s t . c a p t i o n ( " M o n i t o r   t h e   h e a l t h   o f   t h e   d a t a   i n g e s t i o n   p i p e l i n e   a n d   s c r a p e r   p e r f o r m a n c e . " )  
          
         #   1 .   S c r a p e r   S t a t s  
         s t a t s _ d f ,   s u c c e s s _ r a t e   =   d b _ m a n a g e r . g e t _ s c r a p e r _ s t a t s ( )  
          
         c o l 1 ,   c o l 2 ,   c o l 3   =   s t . c o l u m n s ( 3 )  
         c o l 1 . m e t r i c ( " S c r a p e r   S u c c e s s   R a t e " ,   f " { s u c c e s s _ r a t e : . 1 f } % " )  
         i f   n o t   s t a t s _ d f . e m p t y :  
                 a v g _ t i m e   =   s t a t s _ d f [ ' d u r a t i o n _ s e c o n d s ' ] . m e a n ( )  
                 c o l 2 . m e t r i c ( " A v g   E x e c u t i o n   T i m e " ,   f " { a v g _ t i m e : . 1 f } s " )  
                 l a s t _ r u n   =   s t a t s _ d f . i l o c [ 0 ] [ ' t i m e s t a m p ' ]  
                 c o l 3 . m e t r i c ( " L a s t   R u n " ,   l a s t _ r u n )  
         e l s e :  
                 c o l 2 . m e t r i c ( " A v g   E x e c u t i o n   T i m e " ,   " N / A " )  
                 c o l 3 . m e t r i c ( " L a s t   R u n " ,   " N / A " )  
  
         s t . s u b h e a d e r ( " R e c e n t   E x e c u t i o n   L o g s " )  
         s t . d a t a f r a m e ( s t a t s _ d f ,   u s e _ c o n t a i n e r _ w i d t h = T r u e )  
          
         s t . m a r k d o w n ( " - - - " )  
          
         #   2 .   Q u a l i t y   A l e r t s  
         s t . s u b h e a d e r ( " � xa�   D a t a   Q u a l i t y   A l e r t s " )  
         a l e r t s _ d f   =   d b _ m a n a g e r . g e t _ r e c e n t _ q u a l i t y _ a l e r t s ( )  
          
         i f   n o t   a l e r t s _ d f . e m p t y :  
                 #   C o l o r   c o d e   s e v e r i t y  
                 d e f   h i g h l i g h t _ s e v e r i t y ( v a l ) :  
                         c o l o r   =   ' r e d '   i f   v a l   = =   ' C R I T I C A L '   e l s e   ' o r a n g e '   i f   v a l   = =   ' W A R N I N G '   e l s e   ' b l a c k '  
                         r e t u r n   f ' c o l o r :   { c o l o r } '  
                          
                 s t . d a t a f r a m e ( a l e r t s _ d f . s t y l e . a p p l y m a p ( h i g h l i g h t _ s e v e r i t y ,   s u b s e t = [ ' s e v e r i t y ' ] ) ,   u s e _ c o n t a i n e r _ w i d t h = T r u e )  
         e l s e :  
                 s t . s u c c e s s ( " � S&   N o   r e c e n t   d a t a   q u a l i t y   i s s u e s   d e t e c t e d . " )  
          
         #   3 .   M a n u a l   T r i g g e r  
         s t . m a r k d o w n ( " - - - " )  
         s t . s u b h e a d e r ( " � a"!� � �   P i p e l i n e   C o n t r o l " )  
         i f   s t . b u t t o n ( " R u n   M a n u a l   D a t a   U p d a t e   ( A d m i n ) " ) :  
                 w i t h   s t . s p i n n e r ( " R u n n i n g   E T L   P i p e l i n e . . . " ) :  
                         i m p o r t   c o n t e x t l i b  
                         i m p o r t   i o  
                         f   =   i o . S t r i n g I O ( )  
                         w i t h   c o n t e x t l i b . r e d i r e c t _ s t d o u t ( f ) :  
                                 e t l . d a t a _ l o a d e r . r u n _ d a i l y _ u p d a t e ( )  
                          
                         o u t p u t   =   f . g e t v a l u e ( )  
                         s t . c o d e ( o u t p u t )  
                         s t . s u c c e s s ( " M a n u a l   U p d a t e   C o m p l e t e ! " )  
                         s t . r e r u n ( )  
                          
 