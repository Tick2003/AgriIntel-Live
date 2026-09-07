"""
app/terminal_theme.py — AgriIntel Terminal Theme (Facade)
==========================================================
Public API for the terminal UI design system.

Design constants and CSS injection have been extracted into the
``app.theme`` subpackage for maintainability:

    app/theme/tokens.py  — color/typography/motion tokens + Plotly template
    app/theme/css.py     — inject_terminal_css() and full CSS stylesheet

This module re-exports everything for backwards compatibility so that
existing import statements (``from app.terminal_theme import ...``)
continue to work without modification.
"""

# Re-export design tokens
from app.theme.tokens import (
    ACCENT_AMBER,
    ACCENT_BLUE,
    ACCENT_GREEN,
    ACCENT_RED,
    TEXT_MUTED,
)

# Re-export CSS helper

# ─── Reusable Component Helpers ───────────────────────────────────────────────
# (kept here: these use st / pandas and are page-level helpers, not raw tokens)



def get_status_color(level: str) -> str:
    """Return the accent color for a given risk level string."""
    if level.lower() == "low":
        return ACCENT_GREEN
    if level.lower() == "medium":
        return ACCENT_AMBER
    return ACCENT_RED


def render_signal_banner(signal: str, confidence: float = 0.0) -> str:
    """Render a prominent BUY/SELL/HOLD signal banner HTML string."""
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


def render_signal_reasoning(reason: str) -> str:
    """Render inline reasoning below the signal banner."""
    if not reason:
        return ""
    return f"""
        <div class='signal-reasoning'>
            {reason}
        </div>
    """


def render_data_provenance(
    last_date: str,
    source: str = "Agmarknet via data.gov.in",
    data_points: int = 0,
    train_start: str = "",
    train_end: str = "",
) -> str:
    """Render a data provenance bar with freshness timestamp and source badge."""
    parts = [
        f"<span class='provenance-badge'>📅 Data as of: {last_date}</span>",
        f"<span class='provenance-badge'>📡 Source: {source}</span>",
    ]
    if data_points > 0:
        parts.append(f"<span class='provenance-badge'>📊 {data_points:,} data points</span>")
    if train_start and train_end:
        parts.append(
            f"<span class='provenance-badge'>🧠 Model trained: {train_start} → {train_end}</span>"
        )
    return f"<div class='provenance-bar'>{''.join(parts)}</div>"


def render_model_accuracy_badge(mape: float, health_score: float, sample_size: int) -> str:
    """Render a color-coded model accuracy badge."""
    if mape < 8:
        css_class, icon = "model-accuracy-good", "🟢"
    elif mape < 15:
        css_class, icon = "model-accuracy-warn", "🟡"
    else:
        css_class, icon = "model-accuracy-poor", "🔴"

    return f"""
        <div class='model-accuracy-badge {css_class}'>
            {icon} Model Accuracy: MAPE {mape:.1f}%
            &nbsp;|&nbsp; Health: {health_score:.0f}/100
            &nbsp;|&nbsp; Based on {sample_size:,} predictions
        </div>
    """


def render_disclaimer() -> str:
    """Render a persistent disclaimer notice for AI-generated signals."""
    return """
        <div class='disclaimer-bar'>
            ⚖️ All signals and forecasts are AI-generated estimates based on historical data and
            statistical models — they do not constitute financial or trading advice. Always verify
            with local mandi conditions and consult domain experts before making sell/hold decisions.
        </div>
    """


def render_news_card(title: str, date: str, source: str, sentiment: str, url: str) -> str:
    """Render a styled news card with sentiment indicator."""
    sent_icon = "🟢" if sentiment == "Positive" else "🔴" if sentiment == "Negative" else "⚪"
    sent_color = (
        ACCENT_GREEN if sentiment == "Positive"
        else ACCENT_RED if sentiment == "Negative"
        else TEXT_MUTED
    )

    return f"""
        <article class='terminal-panel' style='padding: 16px; margin-bottom: 12px;'
                 role='article' aria-label='News: {title}'>
            <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px;'>
                <span aria-hidden='true'>{sent_icon}</span>
                <time style='color:{ACCENT_BLUE}; font-size: 11px; text-transform: uppercase;
                             letter-spacing: 0.05em;'>{date} | {source}</time>
            </div>
            <h3 style='margin: 0 0 8px 0; font-size: 15px; line-height: 1.4;'>{title}</h3>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span style='color:{sent_color}; font-size: 12px; font-weight: 600;'
                      aria-label='Sentiment: {sentiment}'>{sentiment}</span>
                <a href='{url}' target='_blank' rel='noopener noreferrer'
                   style='color:{ACCENT_GREEN}; text-decoration: none; font-size: 12px;
                          font-weight: 500;'>Read Analysis →</a>
            </div>
        </article>
    """


def render_chat_bubble(role: str, content: str) -> str:
    """Render a styled chat bubble."""
    if role == "user":
        return f"""
            <div style='display: flex; flex-direction: column; align-items: flex-end;
                        margin-bottom: 16px;' role='log' aria-label='Your message'>
                <div class='chat-label' style='color: {ACCENT_BLUE};' aria-hidden='true'>YOU</div>
                <div class='chat-bubble chat-user'>{content}</div>
            </div>
        """
    return f"""
        <div style='display: flex; flex-direction: column; align-items: flex-start;
                    margin-bottom: 16px;' role='log' aria-label='AI response'>
            <div class='chat-label' style='color: {ACCENT_GREEN};' aria-hidden='true'>AGRIINTEL AI</div>
            <div class='chat-bubble chat-ai'>{content}</div>
        </div>
    """


def render_empty_state(icon: str, title: str, message: str) -> str:
    """Render a centered empty state with icon and message."""
    return f"""
        <div class='empty-state'>
            <div class='icon'>{icon}</div>
            <div class='title'>{title}</div>
            <p style='font-size: 13px;'>{message}</p>
        </div>
    """


def render_footer(version: str = "v2.0", data_source: str = "Agmarknet",
                  last_update: str = None) -> str:
    """Render the app footer with disclaimer."""
    update_text = f" | Last DB Update: {last_update}" if last_update else ""
    return f"""
        {render_disclaimer()}
        <div class='app-footer'>
            <p>AgriIntel.in {version} — National Agricultural Intelligence Stack</p>
            <p>Data Source: {data_source} (Pilot Mode){update_text}</p>
            <p style='margin-top: 8px; font-size: 11px;'>Built with ❤️ for Indian Agriculture</p>
        </div>
    """


def render_status_badge(level: str) -> str:
    """Render a colored status badge with icon + text (not color-only, for accessibility)."""
    level_lower = level.lower()
    if level_lower == "low":
        return f"<span class='status-badge status-badge-low'>✅ {level}</span>"
    if level_lower == "medium":
        return f"<span class='status-badge status-badge-medium'>⚠️ {level}</span>"
    return f"<span class='status-badge status-badge-high'>🔴 {level}</span>"


def render_spacer(size: str = "md") -> str:
    """Return an HTML spacer div. Sizes: sm (8px), md (16px), lg (32px), xl (48px)."""
    return f"<div class='spacer-{size}'></div>"


def style_dataframe(df):
    """Apply consistent terminal-style formatting to a pandas DataFrame/Styler."""
    import pandas as pd

    styler = df.style if isinstance(df, pd.DataFrame) else df
    cols = df.columns if isinstance(df, pd.DataFrame) else df.data.columns
    format_dict = {}

    for col in cols:
        col_lower = str(col).lower()
        if any(
            kw in col_lower
            for kw in ["price", "profit", "cost", "p&l", "net_profit",
                       "selling_price", "value", "expected_price"]
        ):
            format_dict[col] = "₹{:.0f}"
        elif any(kw in col_lower for kw in ["distance", "qty", "quantity", "tons"]):
            format_dict[col] = "{:.1f}"
        elif isinstance(df, pd.DataFrame) and df[col].dtype in ["float64", "float32"]:
            format_dict[col] = "{:.2f}"

    if format_dict:
        styler = styler.format(format_dict)
    return styler
