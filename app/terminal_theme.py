import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio

# --- DESIGN TOKENS ---
BG_COLOR = "#111315"
PANEL_COLOR = "#1A1D21"
BORDER_COLOR = "#2A2F36"
TEXT_PRIMARY = "#E6E6E6"
TEXT_SECONDARY = "#A0A6AD"
ACCENT_GREEN = "#3DDC84"
ACCENT_AMBER = "#FFB020"
ACCENT_RED = "#FF4D4F"
ACCENT_BLUE = "#3B82F6"

# --- PLOTLY TERMINAL THEME ---
terminal_template = go.layout.Template()
terminal_template.layout = go.Layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT_SECONDARY, family="Inter, sans-serif"),
    xaxis=dict(
        showgrid=True, gridcolor=BORDER_COLOR, gridwidth=0.5,
        linecolor=BORDER_COLOR, zeroline=False
    ),
    yaxis=dict(
        showgrid=True, gridcolor=BORDER_COLOR, gridwidth=0.5,
        linecolor=BORDER_COLOR, zeroline=False
    ),
    margin=dict(l=40, r=20, t=40, b=40)
)
pio.templates["agriintel_terminal"] = terminal_template

def inject_terminal_css():
    """Injects high-performance minimalistic terminal CSS."""
    st.markdown(f"""
        <style>
            /* Global Overrides */
            .stApp {{
                background-color: {BG_COLOR};
                color: {TEXT_PRIMARY};
            }}
            
            /* Hide Streamlit elements for clean look */
            #MainMenu, footer, header {{visibility: hidden;}}
            
            /* Sidebar Styling */
            section[data-testid="stSidebar"] {{
                background-color: {PANEL_COLOR} !important;
                border-right: 1px solid {BORDER_COLOR};
            }}
            
            /* Metric Cards */
            [data-testid="stMetricValue"] {{
                color: {TEXT_PRIMARY} !important;
                font-size: 1.8rem !important;
                font-weight: 600 !important;
            }}
            [data-testid="stMetricLabel"] {{
                color: {TEXT_SECONDARY} !important;
                font-size: 0.8rem !important;
                text-transform: uppercase;
                letter-spacing: 0.05rem;
            }}
            
            /* Container & Panel Styling */
            div[data-testid="stVerticalBlock"] > div:has(div.element-container) {{
                background-color: transparent;
            }}
            
            /* Custom Panel Class */
            .terminal-panel {{
                background-color: {PANEL_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                padding: 1.5rem;
                margin-bottom: 1rem;
            }}
            
            /* Typography */
            h1, h2, h3 {{
                color: {TEXT_PRIMARY} !important;
                font-family: 'Inter', sans-serif !important;
                font-weight: 500 !important;
            }}
            
            /* Table / Dataframe Styling */
            div[data-testid="stDataFrame"] {{
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
            }}
            
            /* Orb Pulse Effect (Voice UI) */
            @keyframes pulse {{
                0% {{ transform: scale(1); opacity: 0.8; box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }}
                70% {{ transform: scale(1.05); opacity: 1; box-shadow: 0 0 0 20px rgba(59, 130, 246, 0); }}
                100% {{ transform: scale(1); opacity: 0.8; box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }}
            }}
            .voice-orb {{
                width: 120px;
                height: 120px;
                background: radial-gradient(circle, {ACCENT_BLUE} 0%, #1D4ED8 100%);
                border-radius: 50%;
                margin: 40px auto;
                animation: pulse 2.5s infinite ease-in-out;
                filter: blur(2px);
            }}
        </style>
    """, unsafe_allow_html=True)

def get_status_color(level):
    if level.lower() == "low": return ACCENT_GREEN
    if level.lower() == "medium": return ACCENT_AMBER
    return ACCENT_RED
