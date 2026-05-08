import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio

# --- DESIGN TOKENS (PREMIUM INSTITUTIONAL PALETTE) ---
BG_COLOR = "#0D0F12"  # Deeper, richer background
PANEL_COLOR = "rgba(18, 21, 25, 0.8)" # Transparent panel
CARD_BG = "rgba(255, 255, 255, 0.03)"
BORDER_COLOR = "rgba(255, 255, 255, 0.08)"
DIVIDER_COLOR = "rgba(255,255,255,0.05)"

TEXT_PRIMARY = "#F2F2F2"
TEXT_SECONDARY = "#9BA1A8"
TEXT_MUTED = "#6B7280"

ACCENT_GREEN = "#10B981"  # Emerald
ACCENT_AMBER = "#F59E0B"  # Amber
ACCENT_RED = "#EF4444"    # Rose/Red
ACCENT_BLUE = "#3B82F6"   # Royal Blue
ACCENT_GLOW = "rgba(59,130,246,0.12)"
GLASS_BG = "rgba(255, 255, 255, 0.02)"
BACKDROP_BLUR = "blur(12px)"
TRANSITION = "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)"

# --- PLOTLY TERMINAL THEME (BLOOMBERG STYLE) ---
terminal_template = go.layout.Template()
terminal_template.layout = go.Layout(
    plot_bgcolor="rgba(0,0,0,0)", # Fully transparent for glass effect
    paper_bgcolor="rgba(0,0,0,0)", # Fully transparent for glass effect
    font=dict(color="#F2F2F2", family="Public Sans, sans-serif", size=12),
    xaxis=dict(
        showgrid=True, 
        gridcolor="rgba(255, 255, 255, 0.05)", 
        gridwidth=0.5,
        linecolor=BORDER_COLOR, 
        zeroline=False,
        tickfont=dict(size=10, color="#9BA1A8")
    ),
    yaxis=dict(
        showgrid=True, 
        gridcolor="rgba(255, 255, 255, 0.05)", 
        gridwidth=0.5,
        linecolor=BORDER_COLOR, 
        zeroline=False,
        tickfont=dict(size=10, color="#9BA1A8")
    ),
    margin=dict(l=40, r=20, t=40, b=40),
    hoverlabel=dict(bgcolor="#1A1D21", font_size=12, font_family="Public Sans"),
    showlegend=True,
    legend=dict(font=dict(size=10, color="#9BA1A8"), bgcolor="rgba(0,0,0,0)")
)
pio.templates["agriintel_terminal"] = terminal_template
pio.templates.default = "agriintel_terminal"

def inject_terminal_css():
    """Injects high-performance institutional terminal CSS with TOTAL visibility."""
    st.markdown(f"""
        <style>
            /* --- PREMIUM FORMAL UI BUILD 3.0 (CLEANED) --- */
            @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@400;600;700&family=Public+Sans:wght@300;400;500;600;700&display=swap');

            /* FIX: Hide Streamlit icon text fallback (keyboard_double_arrow) */
            /* Sidebar EXPAND button (when sidebar is collapsed) */
            [data-testid="collapsedControl"] {{
                max-width: 44px !important;
                max-height: 44px !important;
                overflow: hidden !important;
            }}
            [data-testid="collapsedControl"] button {{
                max-width: 44px !important;
                max-height: 44px !important;
                overflow: hidden !important;
            }}
            [data-testid="collapsedControl"] button span {{
                visibility: hidden !important;
                max-width: 0 !important;
                overflow: hidden !important;
            }}
            /* Sidebar COLLAPSE button (when sidebar is open) */
            button[data-testid="stSidebarCollapseButton"] {{
                max-width: 44px !important;
                max-height: 44px !important;
                overflow: hidden !important;
            }}
            button[data-testid="stSidebarCollapseButton"] span {{
                visibility: hidden !important;
                max-width: 0 !important;
                overflow: hidden !important;
            }}

            /* --- 1. CORE ARCHITECTURE --- */
            .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
                background-color: {BG_COLOR} !important;
                background-image: 
                    radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.05) 0px, transparent 50%),
                    radial-gradient(at 100% 0%, rgba(16, 185, 129, 0.03) 0px, transparent 50%) !important;
            }}
            
            [data-testid="stSidebar"], [data-testid="stSidebar"] > div {{
                background-color: {PANEL_COLOR} !important;
                backdrop-filter: {BACKDROP_BLUR} !important;
                border-right: 1px solid {BORDER_COLOR} !important;
                transition: {TRANSITION} !important;
            }}

            /* --- 2. GLASSMORPHIC COMPONENTS --- */
            div[data-testid="stExpander"], .terminal-panel {{
                background-color: {GLASS_BG} !important;
                backdrop-filter: {BACKDROP_BLUR} !important;
                border: 1px solid {BORDER_COLOR} !important;
                border-radius: 12px !important;
                margin-bottom: 16px !important;
                transition: {TRANSITION} !important;
            }}
            
            div[data-testid="stExpander"]:hover, .terminal-panel:hover {{
                border-color: rgba(59, 130, 246, 0.3) !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4) !important;
            }}

            div[data-testid="stExpander"] summary {{
                background-color: transparent !important;
                color: {TEXT_PRIMARY} !important;
                font-weight: 600 !important;
                padding: 12px !important;
            }}
            
            /* Target st.code & st.alert */
            [data-testid="stCodeBlock"], [data-testid="stCodeBlock"] pre, [data-testid="stCodeBlock"] code,
            [data-testid="stNotification"], .stAlert {{
                background-color: rgba(0, 0, 0, 0.2) !important;
                color: {TEXT_PRIMARY} !important;
                border: 1px solid {BORDER_COLOR} !important;
                border-radius: 8px !important;
                transition: {TRANSITION} !important;
            }}

            /* --- 3. TYPOGRAPHY & VISUAL DEPTH --- */
            h1, h2, h3 {{
                color: {TEXT_PRIMARY} !important;
                font-family: 'IBM Plex Serif', serif !important;
                font-weight: 700 !important;
                letter-spacing: -0.01em !important;
            }}

            p, span, label, li, .stMarkdown {{
                color: {TEXT_SECONDARY} !important;
                font-family: 'Public Sans', sans-serif !important;
                line-height: 1.6 !important;
            }}
            
            [data-testid="stMetricLabel"] {{
                color: {TEXT_MUTED} !important;
                font-size: 11px !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.12em !important;
                font-family: 'Public Sans', sans-serif !important;
            }}

            [data-testid="stMetricValue"] {{
                color: {TEXT_PRIMARY} !important;
                font-size: 2.2rem !important;
                font-weight: 600 !important;
                font-family: 'IBM Plex Serif', serif !important;
            }}
            
            /* --- 4. WIDGET REFINEMENT --- */
            div[data-baseweb="input"] input, div[data-baseweb="select"] > div {{
                background-color: rgba(255, 255, 255, 0.03) !important;
                color: {TEXT_PRIMARY} !important;
                border: 1px solid {BORDER_COLOR} !important;
                border-radius: 8px !important;
                transition: {TRANSITION} !important;
            }}

            div[data-baseweb="input"] input:focus, div[data-baseweb="select"] > div:focus {{
                border-color: {ACCENT_BLUE} !important;
                box-shadow: 0 0 0 2px {ACCENT_GLOW} !important;
            }}
            
            .stButton > button {{
                background: linear-gradient(135deg, {ACCENT_BLUE}, #2563EB) !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
                padding: 10px 24px !important;
                transition: {TRANSITION} !important;
                text-transform: uppercase !important;
                letter-spacing: 0.05em !important;
                font-size: 12px !important;
            }}
            
            .stButton > button:hover {{
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
                filter: brightness(1.1) !important;
            }}
            
            /* --- 5. CLEANUP & UTILITY --- */
            #MainMenu, footer {{ display: none !important; }}
            [data-testid="stHeader"] {{ 
                background: transparent !important; 
            }}

            
            .stMetric {{
                background: {GLASS_BG} !important;
                padding: 20px !important;
                border-radius: 12px !important;
                border: 1px solid {BORDER_COLOR} !important;
                transition: {TRANSITION} !important;
            }}

            .stMetric:hover {{
                border-color: {ACCENT_BLUE} !important;
            }}

            /* --- 6. GLASS CHARTS --- */
            [data-testid="stPlotlyChart"] {{
                background-color: {GLASS_BG} !important;
                backdrop-filter: {BACKDROP_BLUR} !important;
                border: 1px solid {BORDER_COLOR} !important;
                border-radius: 12px !important;
                padding: 12px !important;
                transition: {TRANSITION} !important;
            }}

            [data-testid="stPlotlyChart"]:hover {{
                border-color: rgba(59, 130, 246, 0.3) !important;
            }}
        </style>
    """, unsafe_allow_html=True)

def get_status_color(level):
    if level.lower() == "low": return ACCENT_GREEN
    if level.lower() == "medium": return ACCENT_AMBER
    return ACCENT_RED
