"""AI Consultant — Multi-turn chatbot for agricultural intelligence."""
import streamlit as st

st.set_page_config(page_title="AgriIntel — Consultant", layout="wide", page_icon="📉", initial_sidebar_state="expanded")

import os as _os, sys as _sys
_repo_root = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
if _repo_root not in _sys.path:
    _sys.path.insert(0, _repo_root)

from app.app_core import init_page, safe_html
from app.terminal_theme import (
    render_chat_bubble,
    render_footer,
)

ctx = init_page()
agents = ctx["agents"]
data = ctx["data"]
forecast_df = ctx["forecast_df"]
risk_info = ctx["risk_info"]
shock_info = ctx["shock_info"]
decision_signal = ctx["decision_signal"]
last_db_update = ctx["last_db_update"]

st.markdown("<h1>🧠 AI Consultant: Strategic Intelligence Chat</h1>", unsafe_allow_html=True)

# Initialize Chat History
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [
        ("ai", "Welcome to the AgriIntel AI Consultant. I can answer questions about market intelligence, risk analysis, and commodity strategy. Ask me anything.")
    ]

# Render Chat History
chat_container = st.container()
with chat_container:
    for role, message in st.session_state.chat_history:
        st.markdown(render_chat_bubble(role, safe_html(message)), unsafe_allow_html=True)

# Quick Action Buttons
st.markdown("---")
qc1, qc2, qc3 = st.columns(3)
with qc1:
    if st.button("📊 Explain Forecast"):
        st.session_state.chat_history.append(("user", "Explain the forecast"))
        try:
            response = agents["chat"].process_query("Explain the current forecast in detail.", data, forecast_df, risk_info, shock_info, decision_signal)
            st.session_state.chat_history.append(("ai", response))
        except Exception as e:
            st.session_state.chat_history.append(("ai", f"Sorry, I encountered an error: {e}"))
        st.rerun()
with qc2:
    if st.button("⚠️ Risk Insights"):
        st.session_state.chat_history.append(("user", "What are the current risk factors?"))
        try:
            response = agents["chat"].process_query("Explain the current risk factors and how they impact my position.", data, forecast_df, risk_info, shock_info, decision_signal)
            st.session_state.chat_history.append(("ai", response))
        except Exception as e:
            st.session_state.chat_history.append(("ai", f"Sorry, I encountered an error: {e}"))
        st.rerun()
with qc3:
    if st.button("💡 Strategy Advice"):
        st.session_state.chat_history.append(("user", "What trading strategy do you recommend?"))
        try:
            response = agents["chat"].process_query("Based on the current data, what trading strategy do you recommend?", data, forecast_df, risk_info, shock_info, decision_signal)
            st.session_state.chat_history.append(("ai", response))
        except Exception as e:
            st.session_state.chat_history.append(("ai", f"Sorry, I encountered an error: {e}"))
        st.rerun()

# Free-form Chat
user_question = st.chat_input("Ask a question about the market...")
if user_question:
    st.session_state.chat_history.append(("user", user_question))
    try:
        response = agents["chat"].process_query(user_question, data, forecast_df, risk_info, shock_info, decision_signal)
        st.session_state.chat_history.append(("ai", response))
    except Exception as e:
        st.session_state.chat_history.append(("ai", f"I'm sorry, I couldn't process that. Error: {e}"))
    st.rerun()

st.markdown(render_footer(last_update=last_db_update), unsafe_allow_html=True)
