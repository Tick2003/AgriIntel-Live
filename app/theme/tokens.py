"""
app/theme/tokens.py — Design System Tokens
==========================================
Single source of truth for all color, typography, and motion constants
used across the AgriIntel terminal UI.

All values follow the Premium Institutional Palette (Dark Mode).
"""

import plotly.graph_objects as go
import plotly.io as pio

# ─── Backgrounds ──────────────────────────────────────────────────────────────
BG_COLOR = "#0D0F12"                        # Deep, rich page background
PANEL_COLOR = "rgba(18, 21, 25, 0.8)"      # Transparent sidebar/panel
BORDER_COLOR = "rgba(255, 255, 255, 0.08)" # Subtle border
DIVIDER_COLOR = "rgba(255,255,255,0.05)"    # Even subtler divider

# ─── Text ─────────────────────────────────────────────────────────────────────
TEXT_PRIMARY = "#F2F2F2"
TEXT_SECONDARY = "#9BA1A8"
TEXT_MUTED = "#8B95A1"   # Minimum WCAG AA 4.5:1 contrast on dark bg

# ─── Accent Colors ────────────────────────────────────────────────────────────
ACCENT_GREEN = "#10B981"                    # Emerald — bullish / success
ACCENT_AMBER = "#F59E0B"                    # Amber   — warning / caution
ACCENT_RED = "#EF4444"                      # Rose    — bearish / error
ACCENT_BLUE = "#3B82F6"                     # Royal Blue — primary CTA
ACCENT_GLOW = "rgba(59,130,246,0.12)"       # Blue glow for focus rings

# ─── Glassmorphism ────────────────────────────────────────────────────────────
GLASS_BG = "rgba(255, 255, 255, 0.02)"
BACKDROP_BLUR = "blur(12px)"

# ─── Motion ───────────────────────────────────────────────────────────────────
TRANSITION = "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)"

# ─── Plotly Terminal Theme (Bloomberg Style) ───────────────────────────────────
terminal_template = go.layout.Template()
terminal_template.layout = go.Layout(
    plot_bgcolor="rgba(0,0,0,0)",   # Fully transparent — glass card effect
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#F2F2F2", family="Public Sans, sans-serif", size=12),
    xaxis=dict(
        showgrid=True,
        gridcolor="rgba(255, 255, 255, 0.05)",
        gridwidth=0.5,
        linecolor=BORDER_COLOR,
        zeroline=False,
        tickfont=dict(size=10, color="#9BA1A8"),
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor="rgba(255, 255, 255, 0.05)",
        gridwidth=0.5,
        linecolor=BORDER_COLOR,
        zeroline=False,
        tickfont=dict(size=10, color="#9BA1A8"),
    ),
    margin=dict(l=40, r=20, t=40, b=40),
    hoverlabel=dict(bgcolor="#1A1D21", font_size=12, font_family="Public Sans"),
    showlegend=True,
    legend=dict(font=dict(size=10, color="#9BA1A8"), bgcolor="rgba(0,0,0,0)"),
)

# Register as the default Plotly template for all AgriIntel charts
pio.templates["agriintel_terminal"] = terminal_template
pio.templates.default = "agriintel_terminal"
