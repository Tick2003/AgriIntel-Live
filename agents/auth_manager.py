import streamlit as st
import os
import bcrypt
import logging
from datetime import datetime, timedelta

try:
    from streamlit_oauth import OAuth2Component
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False

from database import db_manager

logger = logging.getLogger(__name__)

# Load session timeout from config
try:
    from config import settings
    SESSION_TIMEOUT_HOURS = settings.security.session_timeout_hours
    MAX_LOGIN_ATTEMPTS = settings.security.max_login_attempts
except ImportError:
    SESSION_TIMEOUT_HOURS = 8
    MAX_LOGIN_ATTEMPTS = 5


class AuthAgent:
    """
    AGENT 8 — AUTHENTICATION AGENT (v2.0 — Hardened)
    Role: Gatekeeper
    Goal: Manage user login/logout with session timeout and brute-force protection.
    """
    def __init__(self):
        self.auth_key = "user_auth"
        
        # Load Secrets safely
        try:
            self.client_id = st.secrets.get("google_auth", {}).get("client_id")
            self.client_secret = st.secrets.get("google_auth", {}).get("client_secret")
            self.redirect_uri = st.secrets.get("google_auth", {}).get("redirect_uri", "http://localhost:8501")
        except (FileNotFoundError, Exception):
            self.client_id = None
            self.client_secret = None
            self.redirect_uri = "http://localhost:8501"

    def check_session(self):
        """Check if user is logged in and session has not expired."""
        if self.auth_key in st.session_state and st.session_state[self.auth_key].get('logged_in'):
            # Check session timeout
            login_time_str = st.session_state[self.auth_key].get('login_time')
            if login_time_str:
                try:
                    login_time = datetime.fromisoformat(login_time_str)
                    if datetime.now() - login_time > timedelta(hours=SESSION_TIMEOUT_HOURS):
                        st.session_state[self.auth_key] = {'logged_in': False}
                        st.warning("Session expired. Please log in again.")
                        return False
                except (ValueError, TypeError):
                    pass
            return True
        return False

    def get_user_details(self):
        """Get logged in user details."""
        if self.check_session():
            return st.session_state[self.auth_key]
        return None

    def get_role(self):
        details = self.get_user_details()
        return details.get('role', 'Viewer') if details else None

    def login_page(self):
        """Render the login page."""
        st.markdown(f"""
        <style>
        /* Force Root Dark */
        .stApp, [data-testid="stAppViewContainer"] {{
            background-color: #111315 !important;
            color: #E6E6E6 !important;
        }}
        
        /* Extreme Specificity for Hero Card */
        div.tactical-login-card, .stMarkdown div.tactical-login-card {{
            text-align: center !important;
            padding: 50px !important;
            background-color: #1A1D21 !important;
            border: 1px solid #2A2F36 !important;
            border-radius: 12px !important;
            max-width: 650px !important;
            margin: 40px auto !important;
            color: #FFFFFF !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
        }}
        
        .login-title, h1.login-title {{
            font-family: 'Inter', sans-serif !important;
            color: #FFFFFF !important;
            font-size: 28px !important;
            font-weight: 700 !important;
            margin-bottom: 12px !important;
        }}
        
        .login-subtitle, p.login-subtitle {{
            font-size: 1.15em !important;
            color: #C5CBD3 !important;
            opacity: 1 !important;
            margin-bottom: 30px !important;
        }}

        /* Inputs Contrast Force */
        input[type="text"], input[type="password"] {{
            background-color: #1F2329 !important;
            color: #FFFFFF !important;
            border: 1px solid #2A2F36 !important;
        }}
        
        /* Button Contrast Force */
        [data-testid="stForm"] button {{
            background-color: #3B82F6 !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            border: none !important;
        }}
        </style>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 4, 1])
        with col2:
            st.markdown("""
            <div class="tactical-login-card">
                <h1 class="login-title">📉 AgriIntel Terminal v2.0</h1>
                <p class="login-subtitle">National Unified Agricultural Intelligence Stack: Strategic Gateway</p>
                <div style="color: #3B82F6; font-weight: 600; font-size: 1.1em; margin-bottom: 5px;">INSTITUTIONAL ACCESS : AUTHORIZED PERSONNEL ONLY</div>
                <p style="color: #888; font-size: 0.85em;">Tactical Intelligence Infrastructure | Build 782-X</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("") 
            st.write("")
            
            # OAuth Flow
            if self.client_id and self.client_secret and OAUTH_AVAILABLE:
                self._render_google_btn()
            else:
                self._render_db_login()

    def _render_google_btn(self):
        """Real Google OAuth Button"""
        oauth2 = OAuth2Component(
            self.client_id, self.client_secret,
            "https://accounts.google.com/o/oauth2/v2/auth",
            "https://oauth2.googleapis.com/token",
            "https://www.googleapis.com/oauth2/v3/tokeninfo",
            "openid email profile"
        )
        
        result = oauth2.authorize_button(
            name="Login with Google",
            icon="https://www.google.com.tw/favicon.ico",
            redirect_uri=self.redirect_uri,
            scope="openid email profile",
            key="google_oauth_btn",
            extras_params={"prompt": "select_account"},
        )
        
        if result and result.get('token'):
            email = result.get('token', {}).get('email')
            # Check DB
            user = db_manager.get_user_by_email(email)
            
            if user:
                st.session_state[self.auth_key] = {
                    'logged_in': True,
                    'email': email,
                    'role': user['role'],
                    'org_id': user['org_id'],
                    'name': email.split('@')[0],
                    'login_time': datetime.now().isoformat()
                }
                st.rerun()
            else:
                 st.error("User not found in organization. Please contact admin.")

    def _render_db_login(self):
        """Database Login (Fallback) — No pre-filled credentials."""
        st.info("🔐 Secure Enterprise Login")
        
        # Initialize login attempts tracker
        if 'login_attempts' not in st.session_state:
            st.session_state['login_attempts'] = 0
            st.session_state['lockout_until'] = None
        
        # Check lockout
        if st.session_state.get('lockout_until'):
            lockout_until = datetime.fromisoformat(st.session_state['lockout_until'])
            if datetime.now() < lockout_until:
                remaining = (lockout_until - datetime.now()).seconds // 60
                st.error(f"🔒 Account locked due to too many failed attempts. Try again in {remaining + 1} minutes.")
                return
            else:
                st.session_state['login_attempts'] = 0
                st.session_state['lockout_until'] = None
        
        with st.form("login_form"):
            email = st.text_input("Work Email", placeholder="your.email@company.com")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if not email or not password:
                    st.error("Please enter both email and password.")
                    return
                    
                user = db_manager.get_user_by_email(email)
                if user:
                    try:
                        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                            st.session_state[self.auth_key] = {
                                'logged_in': True,
                                'email': user['email'],
                                'role': user['role'],
                                'org_id': user['org_id'],
                                'name': user['email'].split('@')[0],
                                'login_time': datetime.now().isoformat()
                            }
                            st.session_state['login_attempts'] = 0
                            st.success("Authenticated.")
                            st.rerun()
                        else:
                            self._handle_failed_login()
                    except Exception as e:
                        logger.error(f"Auth error: {e}")
                        st.error("Authentication error. Please try again.")
                else:
                    self._handle_failed_login()
    
    def _handle_failed_login(self):
        """Handle failed login with brute-force protection."""
        st.session_state['login_attempts'] = st.session_state.get('login_attempts', 0) + 1
        remaining = MAX_LOGIN_ATTEMPTS - st.session_state['login_attempts']
        
        if remaining <= 0:
            lockout_minutes = 15
            try:
                from config import settings as _cfg
                lockout_minutes = _cfg.security.lockout_duration_minutes
            except ImportError:
                pass
            st.session_state['lockout_until'] = (datetime.now() + timedelta(minutes=lockout_minutes)).isoformat()
            st.error(f"🔒 Too many failed attempts. Account locked for {lockout_minutes} minutes.")
        else:
            st.error(f"Invalid credentials. {remaining} attempts remaining.")

    def logout_button(self):
        """Render logout button in sidebar"""
        user = self.get_user_details()
        if user:
            role = user.get('role', 'Viewer')
            st.sidebar.caption(f"Logged in as: {user.get('email')} ({role})")
        
        if st.sidebar.button("🚪 Logout"):
            st.session_state[self.auth_key] = {'logged_in': False}
            st.rerun()
