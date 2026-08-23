"""Risk Assessment & Shock Monitoring page."""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="AgriIntel — Risk", layout="wide", page_icon="📉", initial_sidebar_state="expanded")

from app.app_core import init_page
from app.terminal_theme import (
    TEXT_PRIMARY, ACCENT_BLUE, DIVIDER_COLOR,
    render_footer, render_status_badge,
)

ctx = init_page()
risk_info = ctx["risk_info"]
shock_info = ctx["shock_info"]
last_db_update = ctx["last_db_update"]

st.markdown("<h1>Risk Assessment & Shock Monitoring</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Market Risk Decomposition")
    score = risk_info['risk_score']
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={'font': {'color': TEXT_PRIMARY, 'size': 36}},
        gauge={
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
    st.markdown(render_status_badge(risk_info['risk_level']), unsafe_allow_html=True)

    st.subheader("Risk Drivers")
    if 'breakdown' in risk_info:
        bd = risk_info['breakdown']
        fig_pie = px.pie(
            names=list(bd.keys()),
            values=list(bd.values()),
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        fig_pie.update_layout(template="agriintel_terminal", showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
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

st.markdown(render_footer(last_update=last_db_update), unsafe_allow_html=True)
