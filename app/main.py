import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.data_health import DataHealthAgent
from agents.forecast_execution import ForecastingAgent
from agents.shock_monitoring import AnomalyDetectionEngine
from agents.risk_scoring import MarketRiskEngine
from agents.explanation_report import AIExplanationAgent
from agents.decision_support import DecisionAgent
from agents.arbitrage_engine import ArbitrageAgent
from agents.intelligence_core import IntelligenceAgent
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

# --- AUTO-UPDATE LOGIC ---
from datetime import datetime
import etl.data_loader
import database.db_manager as db_manager

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

if should_update:
    try:
        with st.spinner("Data is stale (>6 hours). Updating market data..."):
            etl.data_loader.run_daily_update()
            st.cache_resource.clear()
            st.rerun()
    except Exception as e:
        st.error(f"Auto-update failed: {e}")
        print(f"Update Error: {e}")
# -------------------------

# Initialize Agents
@st.cache_resource
def load_agents():
    return {
        "health": DataHealthAgent(),
        "forecast": ForecastingAgent(),
        "shock": AnomalyDetectionEngine(),
        "risk": MarketRiskEngine(),
        "explain": AIExplanationAgent(),
        "decision": DecisionAgent(),
        "arbitrage": ArbitrageAgent(),
        "intel": IntelligenceAgent()
    }

agents = load_agents()

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
    shock_agent = AnomalyDetectionEngine()
    risk_agent = MarketRiskEngine()
    
    shock_info = shock_agent.detect_shocks(data, forecast_df)
    risk_info = risk_agent.calculate_risk_score(shock_info, forecast_df['forecast_price'].std(), data['price'].pct_change().std())
    return shock_info, risk_info

@st.cache_data(ttl=3600)
def run_explanation_agent(commodity, risk_info, shock_info, forecast_df):
    explain_agent = AIExplanationAgent()
    return explain_agent.generate_explanation(commodity, risk_info, shock_info, forecast_df)

@st.cache_data(ttl=3600)
def run_decision_agent(current_price, forecast_df, risk_dict, shock_dict):
    agent = DecisionAgent()
    return agent.get_signal(current_price, forecast_df, risk_dict['risk_score'], shock_dict)

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
page = st.sidebar.radio("Navigate", ["Market Overview", "Price Forecast", "Risk & Shocks", "Compare Markets", "News & Insights", "Model Performance", "Explanation & Insights", "AI Consultant"])


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
    current_price = data['price'].iloc[-1]
    prev_price = data['price'].iloc[-2]
    delta = current_price - prev_price
    
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
    fig.add_trace(go.Scatter(x=data['date'], y=data['price'], mode='lines', name='Price', line_shape='spline', line=dict(color='#2962FF', width=2)))
    fig.update_layout(template="plotly_white", hovermode="x unified", title="Price History (90 Days)")
    st.plotly_chart(fig, use_container_width=True)

# --- PAGE 2: PRICE FORECAST ---
elif page == "Price Forecast":
    st.header("Price Forecast (Next 30 Days)")
    
    # 1. Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['date'], y=data['price'], mode='lines', name='Historical', line_shape='spline', line=dict(color='gray')))
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
    fig.add_trace(go.Scatter(x=data1['date'], y=data1['price'], mode='lines', name=f"{c1} ({m1})", line_shape='spline'))
    fig.add_trace(go.Scatter(x=data2['date'], y=data2['price'], mode='lines', name=f"{c2} ({m2})", line_shape='spline'))
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
    
    # 1. Fetch Data
    data = get_live_data(selected_commodity, selected_mandi)
    
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
        
        improvement = ((mae_base - mae_ml) / mae_base) * 100
        
        # 6. Display Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("ML Accuracy Boost", f"{improvement:.1f}%", "vs Naive Baseline")
        c2.metric("ML Error (MAE)", f"₹{mae_ml:.2f}")
        c3.metric("Baseline Error", f"₹{mae_base:.2f}")
        
        st.info(f"**Evaluation on Hidden Test Set**: We hid the last 30 days of data and asked the AI to predict them. The chart below proves if the AI beat the market.")
        
        # 7. Plot Comparison (Smooth & Professional)
        dates_eval = test_data['date'].values[:min_len]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates_eval, y=actuals, mode='lines', name='Actual Price (Truth)', line_shape='spline', line=dict(color='gray', width=3)))
        fig.add_trace(go.Scatter(x=dates_eval, y=ml_preds, mode='lines', name='AI Forecast', line_shape='spline', line=dict(color='#00C853', width=3, dash='solid')))
        fig.add_trace(go.Scatter(x=dates_eval, y=baseline_preds, mode='lines', name='Naive Baseline', line_shape='spline', line=dict(color='#FF5252', width=2, dash='dot')))
        
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
