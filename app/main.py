"""
AgriIntel.in v2.0 — National Agricultural Intelligence Stack
=============================================================
Entry point. This is the Dashboard (landing page).
All other pages live in `app/pages/`.
"""
import os
import sys

# Ensure repo root is on sys.path so `app.*` imports resolve correctly on
# Streamlit Cloud (which runs this file from /mount/src/<repo>/app/main.py)
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="AgriIntel.in — National Agri Intelligence",
    layout="wide",
    page_icon="📉",
    initial_sidebar_state="expanded"
)

from app.app_core import init_page, safe_html
from app.terminal_theme import (
    ACCENT_AMBER,
    ACCENT_BLUE,
    TEXT_PRIMARY,
    render_data_provenance,
    render_footer,
    render_news_card,
    render_signal_banner,
    render_signal_reasoning,
    render_spacer,
    style_dataframe,
)

# Initialize shared context (auth, sidebar, agents, data)
ctx = init_page()

data = ctx["data"]
forecast_df = ctx["forecast_df"]
risk_info = ctx["risk_info"]
shock_info = ctx["shock_info"]
decision_signal = ctx["decision_signal"]
explanation = ctx["explanation"]
health_status = ctx["health_status"]
signal_stats = ctx["signal_stats"]
agents = ctx["agents"]
selected_commodity = ctx["selected_commodity"]
selected_mandi = ctx["selected_mandi"]
last_db_update = ctx["last_db_update"]
db_manager = ctx["db_manager"]
news_df = ctx["news_df"]
data_points = ctx.get("data_points", 0)

# ─── DASHBOARD PAGE ─────────────────────────────────────────────

st.markdown(f"<h1>{selected_commodity} | {selected_mandi}</h1>", unsafe_allow_html=True)

# Item 1: Data Provenance Bar — show freshness, source, and data points
last_date = data['date'].max().strftime('%d %b %Y')
st.markdown(render_data_provenance(
    last_date=last_date,
    source="Agmarknet via data.gov.in",
    data_points=data_points,
), unsafe_allow_html=True)

# Signal Banner
st.markdown(render_signal_banner(decision_signal['signal'], decision_signal.get('confidence', 0)), unsafe_allow_html=True)

# Item 3: Inline Signal Reasoning — show "why this signal?" directly
if decision_signal.get('reason'):
    st.markdown(render_signal_reasoning(decision_signal['reason']), unsafe_allow_html=True)

# Item 8: Signal Track Record — moved UP, directly below signal for trust
if signal_stats and signal_stats.get('total', 0) > 0:
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Total Signals", signal_stats.get('total', 0))
    sc2.metric("Win Rate", f"{signal_stats.get('win_rate', 0):.1f}%")
    sc3.metric("Profitable", signal_stats.get('profitable', 0))
else:
    st.caption("📊 Signal Track Record: Building history — no past signals evaluated yet.")

st.markdown(render_spacer("sm"), unsafe_allow_html=True)

# 4-Metric Top Row
col1, col2, col3, col4 = st.columns(4)
current_price = data['price'].iloc[-1] if not data.empty else 0
if not data.empty:
    prev_price = data['price'].iloc[-2] if len(data) >= 2 else current_price
    delta = current_price - prev_price
    col1.metric("Current Price", f"₹{current_price:,.0f}", f"{delta:+.2f}")

# Item 5: Forecast range alongside point estimate
if not forecast_df.empty:
    f_price = forecast_df['forecast_price'].iloc[-1]
    f_lower = forecast_df['lower_bound'].iloc[-1]
    f_upper = forecast_df['upper_bound'].iloc[-1]
    f_delta = f_price - current_price
    col2.metric("30-Day Forecast", f"₹{f_price:,.0f}", f"{f_delta:+.2f}")
    col2.caption(f"Range: ₹{f_lower:,.0f} – ₹{f_upper:,.0f}")

col3.metric("Risk Score", f"{risk_info['risk_score']}/100", f"{risk_info['risk_level']}")
col4.metric("Market Regime", risk_info['regime'])

st.markdown(render_spacer("lg"), unsafe_allow_html=True)

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
            st.dataframe(style_dataframe(state_df.head(5)), use_container_width=True)

# ─── AI EXPLANATION ──────────────────────────────────────────────
st.markdown("---")
st.subheader("🤖 AI Market Analysis")

with st.expander("View Detailed Explanation", expanded=True):
    st.write(explanation.get('explanation', 'No explanation available.'))
    next_steps = explanation.get('next_steps', '')
    if next_steps:
        st.info(f"**Next Steps**: {next_steps}")

# ─── NEWS PREVIEW ───────────────────────────────────────────────
st.markdown("---")
st.subheader("📰 Latest Market Intelligence")

if not news_df.empty:
    for _, row in news_df.head(3).iterrows():
        st.markdown(render_news_card(
            safe_html(row['title']),
            safe_html(row['date']),
            safe_html(row['source']),
            row['sentiment'],
            safe_html(row['url'])
        ), unsafe_allow_html=True)

st.markdown(render_footer(last_update=last_db_update), unsafe_allow_html=True)
