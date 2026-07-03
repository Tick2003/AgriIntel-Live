"""Forecast — 30-day strategic price projection with profit analytics."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="AgriIntel — Forecast", layout="wide", page_icon="📉", initial_sidebar_state="expanded")

from app.app_core import init_page
from app.terminal_theme import (
    TEXT_PRIMARY, TEXT_MUTED, ACCENT_BLUE,
    render_spacer, render_footer, style_dataframe,
    render_data_provenance, render_model_accuracy_badge,
)
from agents.performance_monitor import PerformanceMonitor

ctx = init_page()
data = ctx["data"]
forecast_df = ctx["forecast_df"]
agents = ctx["agents"]
selected_commodity = ctx["selected_commodity"]
selected_mandi = ctx["selected_mandi"]
last_db_update = ctx["last_db_update"]
data_points = ctx.get("data_points", 0)

st.markdown("<h1>Strategic Forecasting: 30-Day Projection</h1>", unsafe_allow_html=True)

if forecast_df.empty:
    st.warning("⚠️ Forecast data is not available for this commodity/mandi selection. The forecasting model may need more historical data.")
    st.stop()

# Item 1: Data Provenance Bar — show freshness, source, training window
last_date = data['date'].max().strftime('%d %b %Y')
train_start = data['date'].min().strftime('%d %b %Y')
train_end = data['date'].max().strftime('%d %b %Y')
st.markdown(render_data_provenance(
    last_date=last_date,
    source="Agmarknet via data.gov.in",
    data_points=data_points,
    train_start=train_start,
    train_end=train_end,
), unsafe_allow_html=True)

# Item 2: Model Accuracy Badge — show MAPE and health score
try:
    perf_monitor = PerformanceMonitor()
    health_metrics = perf_monitor.update_metrics(selected_commodity, selected_mandi)
    if health_metrics and health_metrics.get('mape') is not None:
        st.markdown(render_model_accuracy_badge(
            mape=health_metrics['mape'],
            health_score=health_metrics['health_score'],
            sample_size=health_metrics['n'],
        ), unsafe_allow_html=True)
except Exception:
    pass  # Gracefully degrade — don't block the page if performance data is unavailable

st.markdown(render_spacer("sm"), unsafe_allow_html=True)

# 1. Main Forecast Plot
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=data['date'].iloc[-30:], y=data['price'].iloc[-30:],
    mode='lines', name='Historical',
    line=dict(color=TEXT_MUTED, width=1.5)
))
fig.add_trace(go.Scatter(
    x=forecast_df['date'], y=forecast_df['forecast_price'],
    mode='lines', name='AI Forecast',
    line=dict(color=ACCENT_BLUE, width=2, dash='dot')
))
fig.add_trace(go.Scatter(
    x=pd.concat([forecast_df['date'], forecast_df['date'][::-1]]),
    y=pd.concat([forecast_df['upper_bound'], forecast_df['lower_bound'][::-1]]),
    fill='toself', fillcolor='rgba(59, 130, 246, 0.08)',
    line=dict(color='rgba(255,255,255,0)'), name='Confidence band'
))
fig.update_layout(template="agriintel_terminal", height=400, showlegend=True)
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# 2. Profit Analytics
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
        sim_df = agents["decision"].simulate_profit(data['price'].iloc[-1], forecast_df, qty)

        if not sim_df.empty:
            display_df = sim_df.copy()
            if 'Expected P&L' in display_df.columns:
                display_df.rename(columns={'Expected P&L': 'Expected Profit'}, inplace=True)
            if 'Risk Adjusted P&L' in display_df.columns:
                display_df.rename(columns={'Risk Adjusted P&L': 'Risk (±)'}, inplace=True)
            if 'Expected Profit' in display_df.columns:
                display_df['Expected Profit'] = display_df['Expected Profit'].apply(lambda x: f"₹{x:,.2f}")
            if 'Risk (±)' in display_df.columns:
                display_df['Risk (±)'] = display_df['Risk (±)'].apply(lambda x: f"₹{x:,.2f}")
            if 'Expected Price' in display_df.columns:
                display_df['Expected Price'] = display_df['Expected Price'].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(display_df, use_container_width=True)

            if 'Expected Profit' in sim_df.columns:
                best_idx = sim_df['Expected Profit'].idxmax()
                best_scenario = sim_df.loc[best_idx]
                risk_val = best_scenario.get('Risk (±)', 0)
                if 'Risk Adjusted P&L' in best_scenario: risk_val = 0
                if best_scenario['Expected Profit'] > 0:
                    st.success(f"💡 Best Opportunity: Sell in **{best_scenario['Horizon']}** for expected gain of **₹{best_scenario['Expected Profit']:.2f}** (±₹{risk_val:.0f})")
                else:
                    st.error("📉 Forecast suggests prices may fall. Selling now might be best.")
        else:
            st.warning("Not enough forecast data to run analysis.")

st.subheader("Detailed Forecast Data")
st.dataframe(style_dataframe(forecast_df[['date', 'forecast_price', 'lower_bound', 'upper_bound']]), use_container_width=True)

st.markdown(render_footer(last_update=last_db_update), unsafe_allow_html=True)
