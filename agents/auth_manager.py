import streamlit as st
import os
import asyncio
from streamlit_oauth import OAuth2Component

class AuthAgent:
    """
    AGENT 8 — AUTHENTICATION AGENT
    Role: Gatekeeper
    Goal: Manage user login/logout via Google OAuth or Mock Fallback.
    """
    def __init__(self):
        self.auth_key = "user_auth"
        
        # Load Secrets safely
        try:
            self.client_id = st.secrets.get("google_auth", {}).get("client_id")
            self.client_secret = st.secrets.get("google_auth", {}).get("client_secret")
            self.redirect_uri = st.secrets.get("google_auth", {}).get("redirect_uri", "http://localhost:8501")
        except FileNotFoundError:
            self.client_id = None
            self.client_secret = None

    def check_session(self):
        """Check if user is logged in."""
        if self.auth_key in st.session_state and st.session_state[self.auth_key]['logged_in']:
            return True
        return False

    def get_user_email(self):
        """Get logged in user email."""
        if self.check_session():
            return st.session_state[self.auth_key].get('email', 'guest@agriintel.in')
        return None

    def login_page(self):
        """Render the login page."""
        st.markdown("""
        <style>
        .login-container {
            text-align: center;
            padding: 50px;
            background-color: #f0f8ff;
            border-radius: 10px;
            max-width: 600px;
            margin: 0 auto;
            border: 1px solid #dcdcdc;
        }
        .login-title {
            font-family: 'Helvetica Neue', sans-serif;
            color: #2E7D32;
            font-size: 3em;
            margin-bottom: 10px;
        }
        .login-subtitle {
            font-size: 1.2em;
            color: #555;
            margin-bottom: 30px;
        }
        </style>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div class="login-container">
                <h1 class="login-title">🌾 AgriIntel</h1>
                <p class="login-subtitle">Advanced AI Market Intelligence for Indian Agriculture</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("") 
            st.write("")
            
            # OAuth Flow
            if self.client_id and self.client_secret:
                self._render_google_btn()
            else:
                self._render_mock_btn()

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
        
        if result:
            # Decode token (simplified) or use result info
            # Usually result contains 'token' and 'id_token'
            # We assume success if we got a result dict back
            st.session_state[self.auth_key] = {
                'logged_in': True,
                'email': result.get('token', {}).get('email', 'user@google.com'), # Depends on specific provider impl
                'name': 'Google User'
            }
            st.rerun()

    def _render_mock_btn(self):
        """Fallback for when secrets are missing"""
        st.warning("⚠️ Google Secrets not found. Using Guest Mode.")
        
        email = st.text_input("Enter Email (Simulation)", "farmer@agriintel.in")
        
        if st.button("🚀 Login as Guest", type="primary", use_container_width=True):
            st.session_state[self.auth_key] = {
                'logged_in': True,
                'email': email,
                'name': 'Guest User'
            }
            st.rerun()

    def logout_button(self):
        """Render logout button in sidebar"""
        if st.sidebar.button("🚪 Logout"):
            st.session_state[self.auth_key] = {'logged_in': False}
            st.rerun()
