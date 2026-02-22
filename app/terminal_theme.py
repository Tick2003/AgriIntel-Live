import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio

# --- DESIGN TOKENS (STRICT INSTITUTIONAL PALETTE) ---
BG_COLOR = "#111315"
PANEL_COLOR = "#1A1D21"
CARD_BG = "rgba(255, 255, 255, 0.03)"
BORDER_COLOR = "#2A2F36"
DIVIDER_COLOR = "rgba(255,255,255,0.06)"

TEXT_PRIMARY = "#E6E6E6"
TEXT_SECONDARY = "#A0A6AD"
TEXT_MUTED = "#C5CBD3"  # Standardized metadata color

ACCENT_GREEN = "#3DDC84"
ACCENT_AMBER = "#FFB020"
ACCENT_RED = "#FF4D4F"
ACCENT_BLUE = "#3B82F6"
ACCENT_GLOW = "rgba(59,130,246,0.15)"

# ... (Plotly template remains similar, but using TEXT_SECONDARY for ticks)

def inject_terminal_css():
    """Injects high-performance institutional terminal CSS with forced visibility."""
    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Manrope:wght@400;500;600&display=swap');

            /* --- GLOBAL VISIBILITY OVERRIDE --- */
            * {{
                color: {TEXT_PRIMARY} !important;
                -webkit-font-smoothing: antialiased;
                mix-blend-mode: normal !important;
                filter: none !important;
            }}
            
            .stApp {{
                background-color: {BG_COLOR};
                font-family: 'Inter', 'Manrope', sans-serif;
            }}
            
            /* Hide Streamlit elements for clean look */
            #MainMenu, footer, header {{visibility: hidden;}}
            
            /* Sidebar Styling (High Contrast) */
            section[data-testid="stSidebar"] {{
                background-color: {PANEL_COLOR} !important;
                border-right: 1px solid {BORDER_COLOR};
            }}
            section[data-testid="stSidebar"] * {{
                color: {TEXT_PRIMARY} !important;
            }}
            
            /* Dropdown / Selectbox Force Visibility */
            div[data-baseweb="select"] * {{
                color: #FFFFFF !important;
                background-color: {PANEL_COLOR} !important;
            }}
            ul[role="listbox"] * {{
                color: #FFFFFF !important;
                background-color: {PANEL_COLOR} !important;
            }}

            /* Metric Cards & Layout Spacing */
            [data-testid="stMetricValue"] {{
                color: {TEXT_PRIMARY} !important;
                font-size: 32px !important;
                font-weight: 600 !important;
            }}
            [data-testid="stMetricLabel"] {{
                color: {TEXT_SECONDARY} !important;
                font-size: 13px !important;
                font-weight: 400 !important;
                text-transform: uppercase;
                letter-spacing: 0.05rem;
            }}
            
            /* Card & Panel Styling */
            .terminal-panel {{
                background-color: {PANEL_COLOR};
                border: 1px solid {DIVIDER_COLOR};
                border-radius: 4px;
                padding: 24px;
                margin-bottom: 16px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.25);
            }}
            
            /* Typography Hierarchy */
            h1 {{
                font-size: 28px !important;
                font-weight: 600 !important;
                color: {TEXT_PRIMARY} !important;
            }}
            h2, h3 {{
                font-size: 20px !important;
                font-weight: 500 !important;
                color: {TEXT_PRIMARY} !important;
            }}
            
            /* Metadata / Secondary Text Override */
            .metadata-text, .stCaption, caption {{
                color: {TEXT_MUTED} !important;
                font-size: 12px !important;
            }}

            /* Orb Pulse Effect (Voice UI) */
            @keyframes pulse {{
                0% {{ transform: scale(1); opacity: 0.8; }}
                50% {{ transform: scale(1.05); opacity: 1; }}
                100% {{ transform: scale(1); opacity: 0.8; }}
            }}
            .voice-orb {{
                width: 120px;
                height: 120px;
                background: radial-gradient(circle, {ACCENT_BLUE} 0%, #1D4ED8 100%);
                border: 2px solid rgba(59,130,246,0.4);
                border-radius: 50%;
                margin: 40px auto;
                animation: pulse 2.5s infinite ease-in-out;
                box-shadow: 0 0 25px {ACCENT_GLOW};
            }}
            
            /* Table Styling */
            div[data-testid="stDataFrame"] {{
                border: 1px solid {BORDER_COLOR};
                background-color: {PANEL_COLOR};
            }}
            
            /* Tooltip / Hover Force */
            [data-testid="stTooltipContent"] * {{
                color: #FFFFFF !important;
            }}
        </style>
    """, unsafe_allow_html=True)

def get_status_color(level):
    if level.lower() == "low": return ACCENT_GREEN
    if level.lower() == "medium": return ACCENT_AMBER
    return ACCENT_RED
