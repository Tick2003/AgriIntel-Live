# app/theme/__init__.py
# Convenience re-exports so callers can do:
#   from app.theme import BG_COLOR, inject_terminal_css
from .css import inject_terminal_css
from .tokens import (
    ACCENT_AMBER,
    ACCENT_BLUE,
    ACCENT_GLOW,
    ACCENT_GREEN,
    ACCENT_RED,
    BACKDROP_BLUR,
    BG_COLOR,
    BORDER_COLOR,
    DIVIDER_COLOR,
    GLASS_BG,
    PANEL_COLOR,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TRANSITION,
    terminal_template,
)

__all__ = [
    "BG_COLOR", "PANEL_COLOR", "BORDER_COLOR", "DIVIDER_COLOR",
    "TEXT_PRIMARY", "TEXT_SECONDARY", "TEXT_MUTED",
    "ACCENT_GREEN", "ACCENT_AMBER", "ACCENT_RED", "ACCENT_BLUE", "ACCENT_GLOW",
    "GLASS_BG", "BACKDROP_BLUR", "TRANSITION",
    "terminal_template",
    "inject_terminal_css",
]
