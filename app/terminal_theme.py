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
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Manrope:wght@400;500;600&display=swap');

            /* --- TOTAL VISIBILITY ENFORCEMENT --- */
            * {{
                color: {TEXT_PRIMARY} !important;
                -webkit-font-smoothing: antialiased;
            }}
            
            .stApp {{
                background-color: {BG_COLOR} !important;
                font-family: 'Inter', 'Manrope', sans-serif;
            }}
            
            /* Metric Labels (The light grey ones in screenshot) */
            [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {{
                color: #A0A6AD !important;
                font-size: 13px !important;
                font-weight: 500 !important;
                text-transform: uppercase !important;
            }}
            
            /* Sidebar Label & Metadata Visibility */
            section[data-testid="stSidebar"] label, 
            section[data-testid="stSidebar"] .stCaption,
            section[data-testid="stSidebar"] p,
            section[data-testid="stSidebar"] span {{
                color: {TEXT_PRIMARY} !important;
                font-weight: 500 !important;
            }}

            /* Selectbox/Dropdown Labels */
            [data-testid="stWidgetLabel"] p, label p, label {{
                color: {TEXT_PRIMARY} !important;
                font-size: 14px !important;
            }}
            
            /* Sidebar Success/Info Background Fix */
            [data-testid="stSidebar"] [data-testid="stNotification"] {{
                background-color: rgba(25, 28, 33, 0.8) !important;
                border: 1px solid {BORDER_COLOR} !important;
            }}

            /* Button Styling (Total Overhaul) */
            button, .stButton > button {{
                background-color: #1A1D21 !important;
                color: {TEXT_PRIMARY} !important;
                border: 1px solid {BORDER_COLOR} !important;
                border-radius: 4px !important;
                font-weight: 600 !important;
                transition: all 0.2s ease !important;
            }}
            button:hover {{
                border-color: {ACCENT_BLUE} !important;
                background-color: #1F2329 !important;
            }}
            
            /* Metric Values */
            [data-testid="stMetricValue"] {{
                color: {TEXT_PRIMARY} !important;
                font-size: 32px !important;
                font-weight: 600 !important;
            }}
            
            /* Card & Panel Styling */
            .terminal-panel {{
                background-color: {PANEL_COLOR} !important;
                border: 1px solid {BORDER_COLOR} !important;
                padding: 24px !important;
                border-radius: 4px !important;
            }}

            /* Typography Hierarchy */
            h1, h2, h3, .main-title, .section-header {{
                color: {TEXT_PRIMARY} !important;
                font-weight: 600 !important;
            }}
            
            /* Data Source / Captions Visibility */
            .stCaption, caption, .metadata-text {{
                color: #A0A6AD !important;
                font-size: 13px !important;
            }}
            
            /* Chart Background Force (If iframe) */
            .user-select-none {{
                background-color: {BG_COLOR} !important;
            }}
            
            /* Expander Fix (Personalization) */
            [data-testid="stExpander"] {{
                background-color: #1A1D21 !important;
                border: 1px solid {BORDER_COLOR} !important;
            }}

            /* Hide Streamlit components */
            #MainMenu, footer, header {{visibility: hidden !important;}}
        </style>
    """, unsafe_allow_html=True)

def get_status_color(level):
    if level.lower() == "low": return ACCENT_GREEN
    if level.lower() == "medium": return ACCENT_AMBER
    return ACCENT_RED
