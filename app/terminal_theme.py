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

# --- PLOTLY TERMINAL THEME (BLOOMBERG STYLE) ---
terminal_template = go.layout.Template()
terminal_template.layout = go.Layout(
    plot_bgcolor="#111315", # Explicitly forced
    paper_bgcolor="#111315",
    font=dict(color="#E6E6E6", family="Inter, Manrope, sans-serif", size=12),
    xaxis=dict(
        showgrid=True, 
        gridcolor="rgba(255, 255, 255, 0.05)", 
        gridwidth=0.5,
        linecolor=BORDER_COLOR, 
        zeroline=False,
        tickfont=dict(size=10, color="#A0A6AD")
    ),
    yaxis=dict(
        showgrid=True, 
        gridcolor="rgba(255, 255, 255, 0.05)", 
        gridwidth=0.5,
        linecolor=BORDER_COLOR, 
        zeroline=False,
        tickfont=dict(size=10, color="#A0A6AD")
    ),
    margin=dict(l=40, r=20, t=40, b=40),
    hoverlabel=dict(bgcolor=PANEL_COLOR, font_size=12, font_family="Inter"),
    showlegend=True,
    legend=dict(font=dict(size=10, color="#A0A6AD"), bgcolor="rgba(0,0,0,0)")
)
pio.templates["agriintel_terminal"] = terminal_template

def inject_terminal_css():
    """Injects high-performance institutional terminal CSS with TOTAL visibility."""
    st.markdown(f"""
        <style>
            /* --- INSTITUTIONAL UI RECOVERY BUILD 108 --- */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Manrope:wght@400;500;600&display=swap');

            /* --- 1. CORE DARK ARCHITECTURE --- */
            .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
                background-color: {BG_COLOR} !important;
            }}
            
            [data-testid="stSidebar"], [data-testid="stSidebar"] > div {{
                background-color: {PANEL_COLOR} !important;
                border-right: 1px solid {BORDER_COLOR} !important;
            }}

            /* --- 2. EXPANDER, NOTIFICATION & CODE BLOCKS (CRITICAL) --- */
            /* Force Expander Background & Header */
            div[data-testid="stExpander"] {{
                background-color: #1A1D21 !important;
                border: 1px solid {BORDER_COLOR} !important;
                border-radius: 4px !important;
                margin-bottom: 10px !important;
            }}
            
            div[data-testid="stExpander"] summary {{
                background-color: #1A1D21 !important;
                color: {TEXT_PRIMARY} !important;
                font-weight: 600 !important;
            }}
            
            /* Target st.code blocks (The white boxes in screenshot) */
            [data-testid="stCodeBlock"], [data-testid="stCodeBlock"] pre, [data-testid="stCodeBlock"] code {{
                background-color: #0E1117 !important;
                color: {TEXT_PRIMARY} !important;
                border: 1px solid {BORDER_COLOR} !important;
            }}
            
            /* Target the white boxes inside the Notification Log Alert style */
            [data-testid="stNotification"], .stAlert {{
                background-color: #0E1117 !important;
                color: {TEXT_PRIMARY} !important;
                border: 1px solid {BORDER_COLOR} !important;
            }}
            
            [data-testid="stNotification"] * {{
                color: {TEXT_PRIMARY} !important;
            }}

            /* --- 3. TARGETED TEXT VISIBILITY --- */
            h1, h2, h3, p, span, label, li, .stMarkdown, .main-title, .section-header {{
                color: {TEXT_PRIMARY} !important;
                font-family: 'Inter', sans-serif;
            }}
            
            [data-testid="stMetricLabel"], .stCaption, caption, .metadata-text {{
                color: {TEXT_SECONDARY} !important;
                font-size: 13px !important;
                font-weight: 500 !important;
                text-transform: uppercase !important;
            }}

            /* --- 4. WIDGET & INPUT VISIBILITY --- */
            [data-testid="stWidgetLabel"] p, label p, label {{
                color: {TEXT_PRIMARY} !important;
                font-size: 14px !important;
                font-weight: 500 !important;
            }}
            
            div[data-baseweb="input"] input, div[data-baseweb="select"] > div {{
                background-color: #0E1117 !important;
                color: {TEXT_PRIMARY} !important;
                border: 1px solid {BORDER_COLOR} !important;
            }}
            
            /* --- 5. BUTTON & UTILITY --- */
            .stButton > button {{
                background-color: {PANEL_COLOR} !important;
                color: {TEXT_PRIMARY} !important;
                border: 1px solid {BORDER_COLOR} !important;
                font-weight: 600 !important;
            }}
            
            [data-testid="stMetricValue"] {{
                color: {TEXT_PRIMARY} !important;
                font-size: 32px !important;
                font-weight: 600 !important;
            }}
            
            #MainMenu, footer, header {{visibility: hidden !important;}}
            
            iframe {{
                background-color: {BG_COLOR} !important;
            }}
        </style>
    """, unsafe_allow_html=True)

def get_status_color(level):
    if level.lower() == "low": return ACCENT_GREEN
    if level.lower() == "medium": return ACCENT_AMBER
    return ACCENT_RED
