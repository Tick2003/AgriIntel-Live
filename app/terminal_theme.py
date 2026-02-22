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
TEXT_MUTED = "#6B7280"

ACCENT_GREEN = "#3DDC84"
ACCENT_AMBER = "#FFB020"
ACCENT_RED = "#FF4D4F"
ACCENT_BLUE = "#3B82F6"
ACCENT_GLOW = "rgba(59,130,246,0.15)"

# --- PLOTLY TERMINAL THEME (BLOOMBERG STYLE) ---
terminal_template = go.layout.Template()
terminal_template.layout = go.Layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT_SECONDARY, family="Inter, Manrope, sans-serif", size=12),
    xaxis=dict(
        showgrid=True, 
        gridcolor="rgba(255, 255, 255, 0.05)", 
        gridwidth=0.5,
        linecolor=BORDER_COLOR, 
        zeroline=False,
        tickfont=dict(size=10, color=TEXT_MUTED)
    ),
    yaxis=dict(
        showgrid=True, 
        gridcolor="rgba(255, 255, 255, 0.05)", 
        gridwidth=0.5,
        linecolor=BORDER_COLOR, 
        zeroline=False,
        tickfont=dict(size=10, color=TEXT_MUTED)
    ),
    margin=dict(l=40, r=20, t=40, b=40),
    hoverlabel=dict(bgcolor=PANEL_COLOR, font_size=12, font_family="Inter"),
    showlegend=True,
    legend=dict(font=dict(size=10, color=TEXT_SECONDARY), bgcolor="rgba(0,0,0,0)")
)
pio.templates["agriintel_terminal"] = terminal_template

def inject_terminal_css():
    """Injects high-performance institutional terminal CSS."""
    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Manrope:wght@400;500;600&display=swap');

            /* Global Overrides */
            .stApp {{
                background-color: {BG_COLOR};
                color: {TEXT_PRIMARY};
                font-family: 'Inter', 'Manrope', sans-serif;
            }}
            
            /* Hide Streamlit elements for clean look */
            #MainMenu, footer, header {{visibility: hidden;}}
            
            /* Metric Cards & Layout Spacing */
            [data-testid="stMetricValue"] {{
                color: {TEXT_PRIMARY} !important;
                font-size: 32px !important;
                font-weight: 600 !important;
                font-family: 'Inter', sans-serif !important;
            }}
            [data-testid="stMetricLabel"] {{
                color: {TEXT_SECONDARY} !important;
                font-size: 13px !important;
                font-weight: 400 !important;
                text-transform: uppercase;
                letter-spacing: 0.05rem;
            }}
            
            /* Card & Panel Styling (Precise Spacing) */
            .terminal-panel {{
                background-color: {PANEL_COLOR};
                border: 1px solid {DIVIDER_COLOR};
                border-radius: 4px;
                padding: 24px;
                margin-bottom: 16px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.25);
            }}
            
            /* Bloomberg-style Glass Metric */
            div[data-testid="metric-container"] {{
                background-color: {CARD_BG};
                border: 1px solid {DIVIDER_COLOR};
                padding: 16px;
                border-radius: 4px;
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
            p, span, div {{
                font-size: 14px !important;
                font-weight: 400;
            }}
            
            /* Sidebar Styling */
            section[data-testid="stSidebar"] {{
                background-color: {PANEL_COLOR} !important;
                border-right: 1px solid {BORDER_COLOR};
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
        </style>
    """, unsafe_allow_html=True)

def get_status_color(level):
    if level.lower() == "low": return ACCENT_GREEN
    if level.lower() == "medium": return ACCENT_AMBER
    return ACCENT_RED
