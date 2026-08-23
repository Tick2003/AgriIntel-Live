"""Voice Intelligence — IVR interface via Twilio."""
import streamlit as st

st.set_page_config(page_title="AgriIntel — Voice", layout="wide", page_icon="📉", initial_sidebar_state="expanded")

from app.app_core import init_page, safe_html
from app.terminal_theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, ACCENT_BLUE,
    ACCENT_GREEN, BORDER_COLOR,
    render_footer,
)

ctx = init_page()
agents = ctx["agents"]
last_db_update = ctx["last_db_update"]

st.markdown("<h1>🎤 Voice Intelligence: IVR Gateway</h1>", unsafe_allow_html=True)

st.markdown("""
    <div class='voice-orb'></div>
    <p style='text-align: center; font-size: 14px; margin-bottom: 12px;'>Dial In: +91-XXX-XXXXXXX | Status: Live</p>
""", unsafe_allow_html=True)

# Language Selection
lang_sel = st.selectbox("Preferred Language", ["English (en)", "Hindi (hi)", "Marathi (mr)", "Telugu (te)"])
lang_code = lang_sel.split("(")[1].replace(")", "")

# Test Interaction
st.subheader("Test Voice Interaction")
test_query = st.text_input("Simulate a voice query (text):", "What is the price of onion in Nashik?")
if st.button("Submit Query"):
    try:
        from agents.voice_intelligence import VoiceIntelligenceAgent
        voice_agent = VoiceIntelligenceAgent()
        result = voice_agent.process_text_query(test_query, language=lang_code)
        st.markdown(f"""
            <div class='terminal-panel' style='padding: 20px;'>
                <p style='color: {TEXT_MUTED}; font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em;'>AI Response</p>
                <p style='color: {TEXT_PRIMARY}; font-size: 16px; line-height: 1.6;'>{safe_html(result.get('response_text', 'No response.'))}</p>
                <div style='display:flex; gap:16px; margin-top:12px; border-top: 1px solid {BORDER_COLOR}; padding-top:12px;'>
                    <span style='color:{TEXT_MUTED}; font-size: 12px;'>Intent: <b style='color:{ACCENT_BLUE};'>{safe_html(result.get('intent', 'N/A'))}</b></span>
                    <span style='color:{TEXT_MUTED}; font-size: 12px;'>Confidence: <b style='color:{ACCENT_GREEN};'>{result.get('confidence', 0)*100:.0f}%</b></span>
                    <span style='color:{TEXT_MUTED}; font-size: 12px;'>Model: <b>{safe_html(result.get('api_used', 'N/A'))}</b></span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Voice Agent Error: {e}")

# Voice Admin Panel
user_role = ctx.get("user_role", "Viewer")
if user_role == "Admin":
    try:
        from app.voice_admin import render_voice_admin
        render_voice_admin()
    except Exception as e:
        st.caption(f"Voice admin not available: {e}")

st.markdown(render_footer(last_update=last_db_update), unsafe_allow_html=True)
