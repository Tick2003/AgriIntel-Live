"""
app/theme/css.py — CSS Injection Helpers
=========================================
Contains the `inject_terminal_css()` function and all raw CSS strings
for the AgriIntel terminal UI.

Separated from tokens.py (design values) to keep each module single-purpose
and to bring terminal_theme.py below 500 LOC.
"""

import streamlit as st

from .tokens import (
    ACCENT_AMBER,
    ACCENT_BLUE,
    ACCENT_GLOW,
    ACCENT_GREEN,
    ACCENT_RED,
    BACKDROP_BLUR,
    BG_COLOR,
    BORDER_COLOR,
    GLASS_BG,
    PANEL_COLOR,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TRANSITION,
)


def inject_terminal_css() -> None:
    """Inject high-performance institutional terminal CSS into the Streamlit page.

    Call once at the top of each page that uses the terminal theme.
    Preloads fonts via <link> tags (non-render-blocking) and injects a
    comprehensive stylesheet covering all Streamlit widget selectors.
    """
    # Preload fonts via <link> instead of render-blocking @import
    st.markdown("""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@400;600;700&family=Public+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <style>
            /* --- PREMIUM FORMAL UI BUILD 4.0 (AUDITED & IMPROVED) --- */


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

            p, label, li, .stMarkdown {{
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

            /* Buttons */
            .stButton > button,
            button[data-testid="baseButton-secondary"],
            button[data-testid="baseButton-primary"],
            .stFormSubmitButton > button,
            .stDownloadButton > button {{
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

            .stButton > button:hover,
            button[data-testid="baseButton-secondary"]:hover,
            button[data-testid="baseButton-primary"]:hover,
            .stFormSubmitButton > button:hover,
            .stDownloadButton > button:hover {{
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
                filter: brightness(1.1) !important;
            }}

            /* Radio Buttons */
            [data-testid="stRadio"] label,
            [data-testid="stRadio"] div[role="radiogroup"] label {{
                color: {TEXT_SECONDARY} !important;
                font-family: 'Public Sans', sans-serif !important;
            }}
            [data-testid="stRadio"] div[role="radiogroup"] label:hover {{
                color: {TEXT_PRIMARY} !important;
            }}
            [data-testid="stRadio"] div[role="radiogroup"] label[data-checked="true"],
            [data-testid="stRadio"] div[role="radiogroup"] label[aria-checked="true"] {{
                color: {TEXT_PRIMARY} !important;
                font-weight: 600 !important;
            }}

            /* Selectbox */
            [data-testid="stSelectbox"] label {{
                color: {TEXT_MUTED} !important;
                font-size: 11px !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.08em !important;
            }}

            /* Slider */
            [data-testid="stSlider"] label {{
                color: {TEXT_MUTED} !important;
                font-size: 11px !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.08em !important;
            }}

            /* --- 5. SIGNAL BANNERS --- */
            .signal-banner {{
                display: flex;
                align-items: center;
                gap: 16px;
                padding: 20px 28px;
                border-radius: 12px;
                font-size: 22px;
                font-weight: 700;
                font-family: 'IBM Plex Serif', serif;
                letter-spacing: -0.01em;
                margin: 12px 0;
                border: 1px solid transparent;
                animation: signalEntrance 0.5s ease-out;
            }}
            @keyframes signalEntrance {{
                from {{ opacity: 0; transform: translateY(-4px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .signal-buy {{
                background: rgba(16, 185, 129, 0.08);
                border-color: rgba(16, 185, 129, 0.4);
                color: {ACCENT_GREEN};
            }}
            .signal-sell {{
                background: rgba(239, 68, 68, 0.08);
                border-color: rgba(239, 68, 68, 0.4);
                color: {ACCENT_RED};
            }}
            .signal-hold {{
                background: rgba(245, 158, 11, 0.08);
                border-color: rgba(245, 158, 11, 0.4);
                color: {ACCENT_AMBER};
            }}

            /* --- 6. CHAT INTERFACE --- */
            .chat-bubble {{
                max-width: 85%;
                padding: 12px 18px;
                border-radius: 16px;
                font-size: 14px;
                line-height: 1.6;
                font-family: 'Public Sans', sans-serif;
                margin-top: 4px;
            }}
            .chat-user {{
                background: rgba(59, 130, 246, 0.12);
                border: 1px solid rgba(59, 130, 246, 0.25);
                color: {TEXT_PRIMARY};
                border-bottom-right-radius: 4px;
            }}
            .chat-ai {{
                background: rgba(16, 185, 129, 0.08);
                border: 1px solid rgba(16, 185, 129, 0.2);
                color: {TEXT_PRIMARY};
                border-bottom-left-radius: 4px;
            }}
            .chat-label {{
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                font-family: 'Public Sans', sans-serif;
                margin-bottom: 4px;
            }}

            /* --- 7. TABLES --- */
            [data-testid="stDataFrame"] table,
            [data-testid="stTable"] table {{
                color: {TEXT_PRIMARY} !important;
                background-color: transparent !important;
                border-collapse: collapse !important;
            }}
            [data-testid="stDataFrame"] th, [data-testid="stTable"] th {{
                background-color: rgba(255,255,255,0.04) !important;
                color: {TEXT_MUTED} !important;
                font-size: 11px !important;
                text-transform: uppercase !important;
                letter-spacing: 0.08em !important;
                font-family: 'Public Sans', sans-serif !important;
                border-bottom: 1px solid {BORDER_COLOR} !important;
                padding: 10px 16px !important;
                font-weight: 700 !important;
            }}
            [data-testid="stDataFrame"] td, [data-testid="stTable"] td {{
                color: {TEXT_PRIMARY} !important;
                font-family: 'Public Sans', sans-serif !important;
                font-size: 13px !important;
                padding: 10px 16px !important;
                border-bottom: 1px solid {BORDER_COLOR} !important;
                transition: background-color 0.15s ease !important;
            }}
            [data-testid="stDataFrame"] tr:hover td, [data-testid="stTable"] tr:hover td {{
                background-color: rgba(59, 130, 246, 0.05) !important;
            }}

            /* --- 8. PROGRESS BAR --- */
            [data-testid="stProgress"] > div {{
                background-color: rgba(255,255,255,0.06) !important;
                border-radius: 4px !important;
            }}
            [data-testid="stProgress"] > div > div {{
                background: linear-gradient(90deg, {ACCENT_BLUE}, {ACCENT_GREEN}) !important;
                border-radius: 4px !important;
                transition: width 0.3s ease !important;
            }}

            /* --- 9. TABS --- */
            [data-testid="stTabs"] [data-baseweb="tab-list"] {{
                background-color: transparent !important;
                border-bottom: 1px solid {BORDER_COLOR} !important;
            }}
            [data-testid="stTabs"] [data-baseweb="tab"] {{
                background-color: transparent !important;
                color: {TEXT_MUTED} !important;
                font-size: 13px !important;
                font-weight: 600 !important;
                font-family: 'Public Sans', sans-serif !important;
                border-bottom: 2px solid transparent !important;
                padding: 10px 18px !important;
                transition: {TRANSITION} !important;
            }}
            [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {{
                color: {TEXT_PRIMARY} !important;
                border-bottom-color: {ACCENT_BLUE} !important;
            }}
            [data-testid="stTabs"] [data-baseweb="tab"]:hover {{
                color: {TEXT_PRIMARY} !important;
            }}

            /* --- 10. CHARTS (Plotly) --- */
            .js-plotly-plot .plotly .bg {{
                fill: transparent !important;
            }}

            /* --- 11. SPINNER --- */
            [data-testid="stSpinner"] > div {{
                border-top-color: {ACCENT_BLUE} !important;
            }}

            /* --- 12. SIDEBAR NAV LINKS --- */
            [data-testid="stSidebarNavLink"] {{
                color: {TEXT_SECONDARY} !important;
                font-family: 'Public Sans', sans-serif !important;
                font-size: 13px !important;
                font-weight: 500 !important;
                border-radius: 8px !important;
                transition: {TRANSITION} !important;
                padding: 8px 14px !important;
            }}
            [data-testid="stSidebarNavLink"]:hover {{
                background-color: rgba(59, 130, 246, 0.08) !important;
                color: {TEXT_PRIMARY} !important;
            }}
            [data-testid="stSidebarNavLink"][aria-current="page"] {{
                background-color: rgba(59, 130, 246, 0.12) !important;
                color: {ACCENT_BLUE} !important;
                border-left: 3px solid {ACCENT_BLUE} !important;
            }}

            /* --- 13. METRIC DELTA --- */
            [data-testid="stMetricDelta"] svg {{
                display: inline !important;
            }}
            [data-testid="stMetricDelta"] [data-testid="stMetricDeltaIcon-Up"] {{
                color: {ACCENT_GREEN} !important;
            }}
            [data-testid="stMetricDelta"] [data-testid="stMetricDeltaIcon-Down"] {{
                color: {ACCENT_RED} !important;
            }}

            /* --- 14. SCROLLBAR --- */
            ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
            ::-webkit-scrollbar-track {{ background: transparent; }}
            ::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.12); border-radius: 4px; }}
            ::-webkit-scrollbar-thumb:hover {{ background: rgba(255,255,255,0.2); }}

            /* --- 15. FOOTER --- */
            .app-footer {{
                text-align: center;
                padding: 24px 0;
                margin-top: 60px;
                border-top: 1px solid {BORDER_COLOR};
                color: {TEXT_MUTED};
                font-size: 12px;
                font-family: 'Public Sans', sans-serif;
            }}
            .app-footer a {{
                color: {ACCENT_BLUE};
                text-decoration: none;
            }}

            /* --- 16. ALERT PULSE --- */
            @keyframes alertPulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.85; }}
            }}

            /* --- 17. EMPTY STATE --- */
            .empty-state {{
                text-align: center;
                padding: 48px 24px;
                color: {TEXT_MUTED};
            }}
            .empty-state .icon {{
                font-size: 48px;
                margin-bottom: 16px;
                opacity: 0.5;
            }}
            .empty-state .title {{
                font-size: 16px;
                font-weight: 600;
                color: {TEXT_SECONDARY};
                margin-bottom: 8px;
            }}

            /* --- 18. PAGE TRANSITION --- */
            [data-testid="stAppViewBlockContainer"] {{
                animation: pageFadeIn 0.4s ease-out !important;
            }}
            @keyframes pageFadeIn {{
                from {{ opacity: 0; transform: translateY(8px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}

            /* --- 19. SPACING UTILITIES --- */
            .spacer-sm {{ height: 8px; }}
            .spacer-md {{ height: 16px; }}
            .spacer-lg {{ height: 32px; }}
            .spacer-xl {{ height: 48px; }}

            /* --- 20. SIDEBAR SECTION HEADERS --- */
            .nav-section-header {{
                font-size: 10px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.15em;
                color: {TEXT_MUTED};
                padding: 16px 12px 4px 12px;
                font-family: 'Public Sans', sans-serif;
            }}

            /* --- 21. STATUS BADGES --- */
            .status-badge {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 4px 10px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Public Sans', sans-serif;
            }}
            .status-badge-low {{
                background: rgba(16, 185, 129, 0.12);
                color: {ACCENT_GREEN};
                border: 1px solid rgba(16, 185, 129, 0.3);
            }}
            .status-badge-medium {{
                background: rgba(245, 158, 11, 0.12);
                color: {ACCENT_AMBER};
                border: 1px solid rgba(245, 158, 11, 0.3);
            }}
            .status-badge-high {{
                background: rgba(239, 68, 68, 0.12);
                color: {ACCENT_RED};
                border: 1px solid rgba(239, 68, 68, 0.3);
            }}

            /* --- 22. TOAST / NOTIFICATION HIGHLIGHT --- */
            .notification-highlight {{
                animation: highlightPulse 2s ease-out;
            }}
            @keyframes highlightPulse {{
                0% {{ background: rgba(59, 130, 246, 0.15); }}
                100% {{ background: transparent; }}
            }}

            /* --- 23. TRUST & PROVENANCE COMPONENTS --- */
            .provenance-badge {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 4px 12px;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 500;
                font-family: 'Public Sans', sans-serif;
                background: rgba(59, 130, 246, 0.08);
                border: 1px solid rgba(59, 130, 246, 0.2);
                color: {ACCENT_BLUE};
                letter-spacing: 0.02em;
            }}
            .provenance-bar {{
                display: flex;
                align-items: center;
                gap: 16px;
                flex-wrap: wrap;
                padding: 8px 0;
                margin-bottom: 8px;
            }}
            .model-accuracy-badge {{
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 6px 14px;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Public Sans', sans-serif;
                letter-spacing: 0.02em;
            }}
            .model-accuracy-good {{
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.3);
                color: {ACCENT_GREEN};
            }}
            .model-accuracy-warn {{
                background: rgba(245, 158, 11, 0.1);
                border: 1px solid rgba(245, 158, 11, 0.3);
                color: {ACCENT_AMBER};
            }}
            .model-accuracy-poor {{
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.3);
                color: {ACCENT_RED};
            }}
            .disclaimer-bar {{
                text-align: center;
                padding: 10px 16px;
                margin-top: 12px;
                border-radius: 8px;
                background: rgba(245, 158, 11, 0.06);
                border: 1px solid rgba(245, 158, 11, 0.15);
                color: {TEXT_MUTED};
                font-size: 11px;
                font-family: 'Public Sans', sans-serif;
                line-height: 1.5;
            }}
            .signal-reasoning {{
                padding: 10px 16px;
                margin-top: -12px;
                margin-bottom: 16px;
                border-radius: 0 0 12px 12px;
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid {BORDER_COLOR};
                border-top: none;
                font-size: 13px;
                color: {TEXT_SECONDARY};
                font-family: 'Public Sans', sans-serif;
                line-height: 1.6;
            }}
            .agent-status-item {{
                display: flex;
                align-items: center;
                gap: 6px;
                padding: 4px 0;
                font-size: 12px;
                font-family: 'Public Sans', sans-serif;
                color: {TEXT_SECONDARY};
            }}
        </style>
    """, unsafe_allow_html=True)
