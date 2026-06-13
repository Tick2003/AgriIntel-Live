import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio

# --- DESIGN TOKENS (PREMIUM INSTITUTIONAL PALETTE) ---
BG_COLOR = "#0D0F12"  # Deeper, richer background
PANEL_COLOR = "rgba(18, 21, 25, 0.8)" # Transparent panel
BORDER_COLOR = "rgba(255, 255, 255, 0.08)"
DIVIDER_COLOR = "rgba(255,255,255,0.05)"

TEXT_PRIMARY = "#F2F2F2"
TEXT_SECONDARY = "#9BA1A8"
TEXT_MUTED = "#8B95A1"  # Bumped from #6B7280 for WCAG AA 4.5:1 contrast ratio

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
            /* Radio dot visibility */
            [data-testid="stRadio"] div[role="radio"] {{
                border-color: {TEXT_MUTED} !important;
            }}
            [data-testid="stRadio"] div[role="radio"][aria-checked="true"] {{
                border-color: {ACCENT_BLUE} !important;
                background-color: {ACCENT_BLUE} !important;
            }}

            /* Checkbox */
            [data-testid="stCheckbox"] label {{
                color: {TEXT_SECONDARY} !important;
            }}

            /* Number Input steppers */
            button[data-testid="stNumberInput-StepUp"],
            button[data-testid="stNumberInput-StepDown"],
            [data-testid="stNumberInput"] button {{
                color: {TEXT_PRIMARY} !important;
                background-color: rgba(255, 255, 255, 0.05) !important;
                border-color: {BORDER_COLOR} !important;
            }}

            /* File uploader */
            [data-testid="stFileUploader"] {{
                color: {TEXT_SECONDARY} !important;
            }}
            [data-testid="stFileUploader"] section {{
                background-color: rgba(255, 255, 255, 0.03) !important;
                border: 1px dashed {BORDER_COLOR} !important;
                border-radius: 8px !important;
            }}

            /* Chat input */
            [data-testid="stChatInput"] textarea {{
                color: {TEXT_PRIMARY} !important;
                background-color: rgba(255, 255, 255, 0.03) !important;
            }}

            /* Selectbox / Multiselect dropdown text */
            div[data-baseweb="select"] span,
            div[data-baseweb="popover"] li {{
                color: {TEXT_PRIMARY} !important;
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

            /* --- 7. METRIC DELTA COLORS --- */
            [data-testid="stMetricDelta"] {{
                font-weight: 600 !important;
                font-size: 13px !important;
            }}
            [data-testid="stMetricDelta"][data-testid="stMetricDelta"] svg {{
                width: 16px !important;
                height: 16px !important;
            }}

            /* --- 8. DATAFRAME GLASS STYLING --- */
            [data-testid="stDataFrame"], [data-testid="stTable"] {{
                background: {GLASS_BG} !important;
                border: 1px solid {BORDER_COLOR} !important;
                border-radius: 12px !important;
                overflow: hidden !important;
            }}

            /* --- 9. NAVIGATION ACTIVE STATE --- */
            [data-testid="stRadio"] div[role="radiogroup"] label {{
                padding: 8px 12px !important;
                border-radius: 6px !important;
                border-left: 3px solid transparent !important;
                transition: {TRANSITION} !important;
                margin-bottom: 2px !important;
            }}
            [data-testid="stRadio"] div[role="radiogroup"] label:hover {{
                background: rgba(59, 130, 246, 0.06) !important;
                border-left-color: rgba(59, 130, 246, 0.3) !important;
            }}
            [data-testid="stRadio"] div[role="radiogroup"] label[data-checked="true"],
            [data-testid="stRadio"] div[role="radiogroup"] label[aria-checked="true"] {{
                background: rgba(59, 130, 246, 0.08) !important;
                border-left-color: {ACCENT_BLUE} !important;
            }}

            /* --- 10. VOICE ORB --- */
            .voice-orb {{
                width: 140px;
                height: 140px;
                border-radius: 50%;
                background: radial-gradient(circle at 40% 40%,
                    rgba(59, 130, 246, 0.6),
                    rgba(59, 130, 246, 0.15) 60%,
                    rgba(59, 130, 246, 0.03) 100%);
                margin: 40px auto;
                box-shadow:
                    0 0 40px rgba(59, 130, 246, 0.3),
                    0 0 80px rgba(59, 130, 246, 0.1),
                    inset 0 0 30px rgba(59, 130, 246, 0.15);
                animation: orbPulse 3s ease-in-out infinite;
                position: relative;
            }}
            .voice-orb::after {{
                content: '🎤';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: 36px;
            }}
            @keyframes orbPulse {{
                0%, 100% {{
                    transform: scale(1);
                    box-shadow: 0 0 40px rgba(59, 130, 246, 0.3), 0 0 80px rgba(59, 130, 246, 0.1);
                }}
                50% {{
                    transform: scale(1.08);
                    box-shadow: 0 0 60px rgba(59, 130, 246, 0.5), 0 0 120px rgba(59, 130, 246, 0.2);
                }}
            }}

            .voice-orb.listening {{
                background: radial-gradient(circle at 40% 40%,
                    rgba(16, 185, 129, 0.6),
                    rgba(16, 185, 129, 0.15) 60%,
                    rgba(16, 185, 129, 0.03) 100%);
                box-shadow: 0 0 60px rgba(16, 185, 129, 0.4), 0 0 120px rgba(16, 185, 129, 0.15);
                animation: orbPulseActive 1.5s ease-in-out infinite;
            }}
            @keyframes orbPulseActive {{
                0%, 100% {{ transform: scale(1); }}
                50% {{ transform: scale(1.12); }}
            }}

            /* --- 11. SIGNAL BANNER --- */
            .signal-banner {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 16px;
                padding: 16px 24px;
                border-radius: 12px;
                margin-bottom: 20px;
                font-weight: 700;
                font-size: 18px;
                letter-spacing: 0.05em;
                transition: {TRANSITION};
            }}
            .signal-buy {{
                background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(16, 185, 129, 0.05));
                border: 1px solid rgba(16, 185, 129, 0.4);
                color: {ACCENT_GREEN};
            }}
            .signal-sell {{
                background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.05));
                border: 1px solid rgba(239, 68, 68, 0.4);
                color: {ACCENT_RED};
            }}
            .signal-hold {{
                background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(245, 158, 11, 0.05));
                border: 1px solid rgba(245, 158, 11, 0.4);
                color: {ACCENT_AMBER};
            }}

            /* --- 12. CHAT BUBBLES --- */
            .chat-bubble {{
                padding: 12px 16px;
                border-radius: 12px;
                margin-bottom: 12px;
                max-width: 85%;
                line-height: 1.5;
                font-size: 14px;
            }}
            .chat-user {{
                background: rgba(59, 130, 246, 0.12);
                border: 1px solid rgba(59, 130, 246, 0.25);
                color: {TEXT_PRIMARY};
                margin-left: auto;
                border-bottom-right-radius: 4px;
            }}
            .chat-ai {{
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid {BORDER_COLOR};
                color: {TEXT_SECONDARY};
                margin-right: auto;
                border-bottom-left-radius: 4px;
            }}
            .chat-label {{
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                margin-bottom: 4px;
                font-weight: 600;
            }}

            /* --- 13. LOADING SKELETON --- */
            .skeleton {{
                background: linear-gradient(90deg,
                    rgba(255,255,255,0.03) 25%,
                    rgba(255,255,255,0.06) 50%,
                    rgba(255,255,255,0.03) 75%);
                background-size: 200% 100%;
                animation: shimmer 1.5s infinite;
                border-radius: 8px;
            }}
            @keyframes shimmer {{
                0% {{ background-position: 200% 0; }}
                100% {{ background-position: -200% 0; }}
            }}

            /* --- 14. STICKY NAVBAR --- */
            .sticky-nav {{
                position: sticky;
                top: 0;
                z-index: 999;
                backdrop-filter: {BACKDROP_BLUR};
            }}

            /* --- 15. APP FOOTER --- */
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
        </style>
    """, unsafe_allow_html=True)


# --- REUSABLE COMPONENT HELPERS ---

def get_status_color(level):
    if level.lower() == "low": return ACCENT_GREEN
    if level.lower() == "medium": return ACCENT_AMBER
    return ACCENT_RED


def render_signal_banner(signal: str, confidence: float = 0.0):
    """Renders a prominent BUY/SELL/HOLD signal banner."""
    signal_upper = signal.upper().strip()
    css_class = "signal-hold"
    icon = "⏸️"
    label = "HOLD POSITION"
    
    if "BUY" in signal_upper:
        css_class = "signal-buy"
        icon = "📈"
        label = "BUY SIGNAL"
    elif "SELL" in signal_upper:
        css_class = "signal-sell"
        icon = "📉"
        label = "SELL SIGNAL"
    
    conf_text = f" — Confidence {confidence:.0f}%" if confidence else ""
    
    return f"""
        <div class='signal-banner {css_class}' role='status' aria-label='Trading signal: {label}{conf_text}'>
            <span style='font-size: 28px;' aria-hidden='true'>{icon}</span>
            <span>{label}{conf_text}</span>
        </div>
    """


def render_news_card(title, date, source, sentiment, url):
    """Renders a styled news card with sentiment indicator."""
    sent_icon = "🟢" if sentiment == "Positive" else "🔴" if sentiment == "Negative" else "⚪"
    sent_color = ACCENT_GREEN if sentiment == "Positive" else ACCENT_RED if sentiment == "Negative" else TEXT_MUTED
    
    return f"""
        <article class='terminal-panel' style='padding: 16px; margin-bottom: 12px;' role='article' aria-label='News: {title}'>
            <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px;'>
                <span aria-hidden='true'>{sent_icon}</span>
                <time style='color:{ACCENT_BLUE}; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em;'>{date} | {source}</time>
            </div>
            <h3 style='margin: 0 0 8px 0; font-size: 15px; line-height: 1.4;'>{title}</h3>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span style='color:{sent_color}; font-size: 12px; font-weight: 600;' aria-label='Sentiment: {sentiment}'>{sentiment}</span>
                <a href='{url}' target='_blank' rel='noopener noreferrer' style='color:{ACCENT_GREEN}; text-decoration: none; font-size: 12px; font-weight: 500;'>Read Analysis →</a>
            </div>
        </article>
    """


def render_chat_bubble(role, content):
    """Renders a styled chat bubble."""
    if role == "user":
        return f"""
            <div style='display: flex; flex-direction: column; align-items: flex-end; margin-bottom: 16px;' role='log' aria-label='Your message'>
                <div class='chat-label' style='color: {ACCENT_BLUE};' aria-hidden='true'>YOU</div>
                <div class='chat-bubble chat-user'>{content}</div>
            </div>
        """
    else:
        return f"""
            <div style='display: flex; flex-direction: column; align-items: flex-start; margin-bottom: 16px;' role='log' aria-label='AI response'>
                <div class='chat-label' style='color: {ACCENT_GREEN};' aria-hidden='true'>AGRIINTEL AI</div>
                <div class='chat-bubble chat-ai'>{content}</div>
            </div>
        """


def render_empty_state(icon, title, message):
    """Renders a centered empty state with icon and message."""
    return f"""
        <div class='empty-state'>
            <div class='icon'>{icon}</div>
            <div class='title'>{title}</div>
            <p style='font-size: 13px;'>{message}</p>
        </div>
    """


def render_footer(version="v2.0", data_source="Agmarknet", last_update=None):
    """Renders the app footer."""
    update_text = f" | Last DB Update: {last_update}" if last_update else ""
    return f"""
        <div class='app-footer'>
            <p>AgriIntel.in {version} — National Agricultural Intelligence Stack</p>
            <p>Data Source: {data_source} (Pilot Mode){update_text}</p>
            <p style='margin-top: 8px; font-size: 11px;'>Built with ❤️ for Indian Agriculture</p>
        </div>
    """


def render_status_badge(level: str) -> str:
    """Renders a colored status badge with icon + text for accessibility (not color-only)."""
    level_lower = level.lower()
    if level_lower == "low":
        return f"<span class='status-badge status-badge-low'>✅ {level}</span>"
    elif level_lower == "medium":
        return f"<span class='status-badge status-badge-medium'>⚠️ {level}</span>"
    else:
        return f"<span class='status-badge status-badge-high'>🔴 {level}</span>"


def render_spacer(size: str = "md") -> str:
    """Returns an HTML spacer div. Sizes: sm (8px), md (16px), lg (32px), xl (48px)."""
    return f"<div class='spacer-{size}'></div>"


def style_dataframe(df):
    """Applies a consistent terminal style formatting to a pandas DataFrame/Styler."""
    import pandas as pd
    styler = df.style if isinstance(df, pd.DataFrame) else df
    cols = df.columns if isinstance(df, pd.DataFrame) else df.data.columns
    format_dict = {}
    
    for col in cols:
        col_lower = str(col).lower()
        # Format prices/profits/costs with Rupee symbol
        if any(keyword in col_lower for keyword in ['price', 'profit', 'cost', 'p&l', 'net_profit', 'selling_price', 'value', 'expected_price']):
            format_dict[col] = "₹{:.0f}"
        # Format distances and decimals
        elif any(keyword in col_lower for keyword in ['distance', 'qty', 'quantity', 'tons']):
            format_dict[col] = "{:.1f}"
        elif isinstance(df, pd.DataFrame) and df[col].dtype in ['float64', 'float32']:
            format_dict[col] = "{:.2f}"
            
    if format_dict:
        styler = styler.format(format_dict)
    return styler

