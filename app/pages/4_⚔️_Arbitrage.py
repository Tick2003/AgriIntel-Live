"""Arbitrage — Compare markets and find arbitrage opportunities."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="AgriIntel — Arbitrage", layout="wide", page_icon="📉", initial_sidebar_state="expanded")

from app.app_core import init_page
from app.utils import get_live_data
from app.terminal_theme import (
    TEXT_PRIMARY, ACCENT_GREEN, ACCENT_BLUE,
    render_footer, style_dataframe,
)

ctx = init_page()
data = ctx["data"]
agents = ctx["agents"]
shock_info = ctx["shock_info"]
selected_commodity = ctx["selected_commodity"]
selected_mandi = ctx["selected_mandi"]
db_commodities = ctx["db_commodities"]
db_mandis = ctx["db_mandis"]
last_db_update = ctx["last_db_update"]

st.markdown("<h1>Compare Markets & Arbitrage Analysis</h1>", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def fetch_arbitrage_snapshot(commodity, all_mandis):
    def _fetch_single(mandi):
        try:
            return get_live_data(commodity, mandi)
        except Exception:
            return pd.DataFrame()
    frames = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        results = executor.map(_fetch_single, all_mandis)
        for df in results:
            if not df.empty:
                frames.append(df)
    if frames:
        return pd.concat(frames)
    return pd.DataFrame()

# Performance Optimized Regional Scan
st.markdown("<div class='terminal-panel'>", unsafe_allow_html=True)
st.subheader(f"Strategy Scan: {selected_commodity} Regional Corridor")
st.caption(f"Base Origin: {selected_mandi} | Scan Depth: Cluster A")

with st.spinner("Executing tactical scan..."):
    scan_mandis = db_mandis[:12] if len(db_mandis) > 12 else db_mandis
    snapshot_df = fetch_arbitrage_snapshot(selected_commodity, scan_mandis)

    if not snapshot_df.empty:
        arb_res = agents['arbitrage'].find_opportunities(
            selected_commodity, selected_mandi, snapshot_df, shock_info, {}
        )
        if not arb_res.empty:
            available_cols = [c for c in arb_res.columns if c in ['Target Mandi', 'Net Profit/Qt', 'Distance (km)', 'Target Price', 'Current Price', 'Confidence']]
            fmt = {}
            if 'Net Profit/Qt' in available_cols: fmt['Net Profit/Qt'] = '₹{:.0f}'
            if 'Target Price' in available_cols: fmt['Target Price'] = '₹{:.0f}'
            if 'Current Price' in available_cols: fmt['Current Price'] = '₹{:.0f}'
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
if data1.empty or data2.empty:
    st.warning("⚠️ Insufficient data for one or both selections. Please choose different commodity/mandi pairs.")
else:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data1['date'], y=data1['price'], mode='lines', name=f"{c1}", line=dict(color=TEXT_PRIMARY, width=1.5)))
    fig.add_trace(go.Scatter(x=data2['date'], y=data2['price'], mode='lines', name=f"{c2}", line=dict(color=ACCENT_BLUE, width=1.5, dash='dot')))
    fig.update_layout(template="agriintel_terminal", hovermode="x unified", transition_duration=0)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

st.markdown(render_footer(last_update=last_db_update), unsafe_allow_html=True)
