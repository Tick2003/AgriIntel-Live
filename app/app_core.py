"""
app/app_core.py — Shared Application Core
=============================================
Contains auth, sidebar config, agent initialization, and data loading
shared across all pages in the multi-page Streamlit app.
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import html as html_module
import logging
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Sanitize external data for safe HTML rendering
def safe_html(text):
    """Escape HTML to prevent XSS in unsafe_allow_html blocks."""
    if text is None:
        return ""
    return html_module.escape(str(text))


def init_page():
    """
    Initialize page with auth, sidebar, agents, and data loading.
    Must be called at the top of every page.
    Returns a dict with all shared context, or calls st.stop() if auth fails.
    """
    from agents.data_health import DataHealthAgent
    from agents.forecast_execution import ForecastingAgent
    from agents.shock_monitoring import AnomalyDetectionEngine
    from agents.risk_scoring import MarketRiskEngine
    from agents.explanation_report import AIExplanationAgent
    from agents.arbitrage_engine import ArbitrageAgent
    from agents.intelligence_core import IntelligenceAgent
    from agents.user_profile import UserProfileAgent
    from agents.notification_service import NotificationService
    from agents.auth_manager import AuthAgent
    from agents.language_manager import LanguageManager
    from agents.chatbot_engine import ChatbotEngine
    from agents.optimization_engine import OptimizationEngine
    from agents.business_engine import B2BMatcher, FintechEngine
    from agents.decision_support import DecisionAgent
    from app.utils import get_live_data, get_news_feed, get_weather_data, get_db_options
    import database.db_manager as db_manager
    from app.terminal_theme import (
        inject_terminal_css, BG_COLOR, BORDER_COLOR,
        TEXT_PRIMARY, TEXT_SECONDARY, ACCENT_BLUE,
        render_footer,
    )

    inject_terminal_css()

    # --- BOOT-TIME CACHE CLEAR (Prevents Stale Data on Redeploy) ---
    if 'boot_cache_cleared' not in st.session_state:
        st.cache_data.clear()
        st.session_state['boot_cache_cleared'] = True

    # Load Lang Manager
    lang_manager = LanguageManager()

    # --- TOP NAVIGATION (SIMULATED NAVBAR) ---
    st.markdown(f"""
        <div style='display: flex; align-items: center; justify-content: space-between; height: 60px; background-color: {BG_COLOR}; border-bottom: 1px solid {BORDER_COLOR}; margin-bottom: 24px; padding: 0 24px;'>
            <div style='font-size: 20px; font-weight: 600; color: {TEXT_PRIMARY};'>AgriIntel.in <span style='color: {ACCENT_BLUE}; font-size: 14px;'>v2.0</span></div>
            <div style='color: {TEXT_SECONDARY}; font-size: 13px;'>{datetime.now().strftime('%d %b %Y | %H:%M:%S')}</div>
        </div>
    """, unsafe_allow_html=True)

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

    st.sidebar.image("logo.png", use_container_width=True)
    st.sidebar.title("📉 Terminal Config")
    auth_agent.logout_button()

    # Sidebar
    st.sidebar.header("Configuration")

    try:
        from config import settings as _cfg
        LOCK_FILE = _cfg.etl.lock_file
    except ImportError:
        LOCK_FILE = ".update.lock"

    # Thread-safe lock file helper
    def _acquire_lock():
        """Try to atomically create lock file. Returns True if acquired."""
        try:
            fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(datetime.now()).encode())
            os.close(fd)
            return True
        except FileExistsError:
            return False
        except OSError:
            return False

    def _release_lock():
        """Remove lock file."""
        try:
            if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)
        except OSError:
            pass

    # Debug / Manual Update
    if st.sidebar.button("🔄 Force Data Update"):
        if _acquire_lock():
            try:
                import etl.data_loader
                def manual_background_update():
                    try:
                        etl.data_loader.run_daily_update(skip_swarm=False)
                        db_manager.set_last_update()
                    except Exception as e:
                        logger.error(f"Manual Update Failed: {e}")
                    finally:
                        _release_lock()

                threading.Thread(target=manual_background_update, daemon=True).start()
                st.sidebar.success("Update triggered in background!")
                st.cache_data.clear()
            except Exception as e:
                _release_lock()
                st.sidebar.error(f"Manual trigger failed: {e}")
        else:
            st.sidebar.warning("Update already in progress...")

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
    try:
        _staleness_hours = _cfg.etl.staleness_threshold_hours
    except (NameError, AttributeError):
        _staleness_hours = 6

    should_update = False
    if not last_db_update:
        should_update = True
    else:
        try:
            dt = datetime.strptime(last_db_update, "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - dt).total_seconds() > _staleness_hours * 3600:
                should_update = True
        except (ValueError, TypeError):
            should_update = True

    if should_update and _acquire_lock():
        def background_update():
            import etl.data_loader
            import database.db_manager as dbm
            try:
                etl.data_loader.run_daily_update(skip_swarm=True)
                dbm.set_last_update()
            except Exception as e:
                logger.error(f"Background Update Error: {e}")
            finally:
                _release_lock()

        threading.Thread(target=background_update, daemon=True).start()
        st.sidebar.info("🚀 System initializing data in background.")

    if os.path.exists(LOCK_FILE):
        st.sidebar.warning("⏳ Intelligence agents are active in background.")

    # Initialize Agents
    @st.cache_resource
    def load_shared_agents():
        """Load shared (non-user-specific) agents. Cached across all sessions."""
        return {
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

    agents = load_shared_agents()
    # User-specific agent (NOT cached globally — per session)
    if 'user_profile_agent' not in st.session_state:
        st.session_state['user_profile_agent'] = UserProfileAgent(user_id=user_email)
    agents["profile"] = st.session_state['user_profile_agent']

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

    # --- Load Data & Run Agents ---
    @st.cache_data(ttl=600)
    def fetch_and_process_data(commodity, mandi, db_update_time):
        """Fetches live data with cache-busting based on DB update time."""
        return get_live_data(commodity, mandi)

    agent_errors = []  # Track agent failures for transparency (Item 7)

    with st.spinner("Analyzing Market Intelligence & Executing ML Projections..."):
        try:
            data = fetch_and_process_data(selected_commodity, selected_mandi, last_db_update)
        except Exception as e:
            data = pd.DataFrame()
            agent_errors.append(f"Data Loader: {str(e)[:100]}")

        if data.empty:
            st.warning("⚠️ No market data available for this commodity/mandi selection. Please try a different selection or wait for the next data update.")
            st.stop()

        last_date = data['date'].max().strftime('%Y-%m-%d')

        # Run Agents — track errors for transparency
        try:
            health_status = agents["health"].check_daily_completeness(data)
        except Exception as e:
            health_status = {}
            agent_errors.append(f"Data Health: {str(e)[:100]}")
        try:
            forecast_df = agents["forecast"].generate_forecasts(data, selected_commodity, selected_mandi)
        except Exception as e:
            forecast_df = pd.DataFrame()
            agent_errors.append(f"Forecast Engine: {str(e)[:100]}")

        # --- Calculate Risk Inputs ---
        news_df = get_news_feed()
        sentiment_score = 0
        if not news_df.empty:
            sent_map = {"Positive": 1, "Negative": -1, "Neutral": 0}
            sentiment_score = news_df['sentiment'].map(sent_map).mean()
            if pd.isna(sentiment_score): sentiment_score = 0

        arrival_anomaly = 0
        if len(data) > 30:
            recent_arrival = data['arrival'].iloc[-1]
            avg_arrival = data['arrival'].iloc[-30:].mean()
            if avg_arrival > 0:
                arrival_anomaly = (recent_arrival - avg_arrival) / avg_arrival

        weather_risk = 0
        w_df = get_weather_data()
        if not w_df.empty:
            w = w_df.iloc[-1]
            if w['temperature'] > 40 or w['rainfall'] > 50:
                weather_risk = 1.0

        try:
            shock_info = agents["shock"].detect_shocks(data, forecast_df)
            risk_info = agents["risk"].calculate_risk_score(
                shock_info,
                forecast_df['forecast_price'].std() if not forecast_df.empty else 0,
                data['price'].pct_change().std(),
                sentiment_score,
                arrival_anomaly,
                weather_risk
            )
        except Exception as e:
            shock_info = {"is_shock": False, "severity": "None", "details": "", "shocks": []}
            risk_info = {"risk_score": 0, "risk_level": "Low", "regime": "Unknown", "explanation_tags": [], "breakdown": {}}
            agent_errors.append(f"Risk/Shock Engine: {str(e)[:100]}")

        # Check Notifications (Real-time)
        try:
            agents["notify"].check_triggers(shock_info, risk_info, selected_commodity, selected_mandi)
        except Exception:
            pass  # Non-critical — notification failures don't affect analysis

        try:
            decision_signal = agents["decision"].get_signal(data['price'].iloc[-1], forecast_df, risk_info, shock_info)
        except Exception as e:
            decision_signal = {"signal": "HOLD", "confidence": 0}
            agent_errors.append(f"Decision Engine: {str(e)[:100]}")
        try:
            explanation = agents["explain"].generate_explanation(selected_commodity, risk_info, shock_info, forecast_df)
        except Exception as e:
            explanation = {"explanation": "Analysis temporarily unavailable.", "next_steps": "Please try refreshing the page."}
            agent_errors.append(f"Explanation Engine: {str(e)[:100]}")

    st.caption(f"Data Source: Agmarknet (Pilot Mode) | Last Updated: {last_date}")

    # --- Item 6: Data Health Badge in Sidebar ---
    if health_status:
        health_stat = health_status.get('status', 'OK')
        if health_stat == 'OK':
            st.sidebar.success("✅ Data Integrity: Verified")
        elif health_stat == 'Warning':
            issues_text = "; ".join(health_status.get('issues', []))
            st.sidebar.warning(f"⚠️ Data Quality: {issues_text}" if issues_text else "⚠️ Data Quality: Minor issues detected")
        else:
            issues_text = "; ".join(health_status.get('issues', []))
            st.sidebar.error(f"🔴 Data Quality: {issues_text}" if issues_text else "🔴 Data Quality: Critical issues")

    # --- Item 7: Surface Agent Errors (no silent fails) ---
    if agent_errors:
        with st.sidebar.expander(f"⚠️ Agent Status ({len(agent_errors)} issue{'s' if len(agent_errors) > 1 else ''})", expanded=False):
            for err in agent_errors:
                st.warning(err)

    # --- SIGNAL LOGGING ---
    try:
        last_date_str = data['date'].iloc[-1].strftime("%Y-%m-%d")
    except Exception:
        last_date_str = datetime.now().strftime("%Y-%m-%d")

    try:
        db_manager.log_signal(last_date_str, selected_commodity, selected_mandi, decision_signal['signal'], data['price'].iloc[-1])
    except Exception as e:
        logger.error(f"Logging Error: {e}")

    signal_stats = {}
    try:
        if hasattr(db_manager, 'get_signal_stats'):
            signal_stats = db_manager.get_signal_stats(selected_commodity, selected_mandi)
    except Exception as e:
        logger.error(f"Stats Error: {e}")

    # Return all shared context
    return {
        "data": data,
        "forecast_df": forecast_df,
        "risk_info": risk_info,
        "shock_info": shock_info,
        "decision_signal": decision_signal,
        "explanation": explanation,
        "health_status": health_status,
        "signal_stats": signal_stats,
        "agents": agents,
        "selected_commodity": selected_commodity,
        "selected_mandi": selected_mandi,
        "db_commodities": db_commodities,
        "db_mandis": db_mandis,
        "last_db_update": last_db_update,
        "user_email": user_email,
        "user_role": user_role,
        "news_df": news_df,
        "db_manager": db_manager,
        "agent_errors": agent_errors,
        "data_points": len(data),
    }

