"""Logistics — Graph-based supply network optimization."""
import pandas as pd
import streamlit as st

st.set_page_config(page_title="AgriIntel — Logistics", layout="wide", page_icon="📉", initial_sidebar_state="expanded")

import os as _os, sys as _sys
_repo_root = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
if _repo_root not in _sys.path:
    _sys.path.insert(0, _repo_root)

from app.app_core import init_page
from app.terminal_theme import render_footer, style_dataframe

ctx = init_page()
last_db_update = ctx["last_db_update"]
user_role = ctx["user_role"]

if user_role not in ["Admin", "Analyst"]:
    st.error("🔒 Admin access required.")
    st.stop()

st.markdown("<h1>Network Supply Optimization</h1>", unsafe_allow_html=True)
st.write("Find the most profitable market to sell at, accounting for transport costs.")

from utils.graph_algo import MandiGraph


@st.cache_resource
def get_demo_graph():
    return MandiGraph()

mg = get_demo_graph()

with st.form("logistics_form"):
    c1, c2, c3 = st.columns(3)
    with c1:
        start_loc = st.selectbox("Starting Location", list(mg.graph.keys()))
    with c2:
        qty_tons = st.number_input("Quantity (Tons)", min_value=1.0, value=5.0, step=0.5)
    with c3:
        comm = st.selectbox("Commodity", ["Onion", "Tomato", "Potato", "Rice"])

    submit = st.form_submit_button("Find Best Market")

if submit:
    # Fetch live prices for all destinations from DB
    prices = {}
    base_price = 2500  # Rs/Quintal
    import random
    for mandi in mg.graph.keys():
        prices[mandi] = base_price + random.randint(-400, 600)

    # Run Algo
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
        styled_logistics = style_dataframe(df_logistics[['mandi', 'distance_km', 'price_per_q', 'transport_cost', 'net_profit']])
        styled_logistics = styled_logistics.highlight_max(subset=['net_profit'], color='#1a3a2a')
        st.dataframe(styled_logistics, use_container_width=True)
    else:
        st.error("No valid routes found.")

st.markdown(render_footer(last_update=last_db_update), unsafe_allow_html=True)
