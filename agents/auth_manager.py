import streamlit as st
import os
import asyncio
from streamlit_oauth import OAuth2Component
from database import db_manager

class AuthAgent:
    """
    AGENT 8 — AUTHENTICATION AGENT
    Role: Gatekeeper
    Goal: Manage user login/logout via Google OAuth or DB Auth.
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

    def get_user_details(self):
        """Get logged in user details."""
        if self.check_session():
            return st.session_state[self.auth_key]
        return None

    def get_role(self):
        return self.get_user_details().get('role', 'Viewer') if self.check_session() else None

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
                <p><b>SaaS Enterprise Edition</b></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("") 
            st.write("")
            
            # OAuth Flow
            if self.client_id and self.client_secret:
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
                    'name': email.split('@')[0]
                }
                st.rerun()
            else:
                 st.error("User not found in organization. Please contact admin.")

    def _render_db_login(self):
        """Database Login (Fallback)"""
        st.info("🔐 Secure Enterprise Login")
        
        with st.form("login_form"):
            email = st.text_input("Work Email", "admin@agriintel.in")
            password = st.text_input("Password", type="password", value="admin123")
            submit = st.form_submit_button("Login")
            
            if submit:
                user = db_manager.get_user_by_email(email)
                if user and user['password_hash'] == password:
                     st.session_state[self.auth_key] = {
                        'logged_in': True,
                        'email': user['email'],
                        'role': user['role'],
                        'org_id': user['org_id'],
                        'name': user['email'].split('@')[0]
                    }
                     st.success("Authenticated.")
                     st.rerun()
                else:
                    st.error("Invalid credentials.")

    def logout_button(self):
        """Render logout button in sidebar"""
        user = self.get_user_details()
        role = user.get('role', 'Viewer') if user else ''
        st.sidebar.caption(f"Logged in as: {user.get('email')} ({role})")
        
        if st.sidebar.button("🚪 Logout"):
            st.session_state[self.auth_key] = {'logged_in': False}
            st.rerun()
