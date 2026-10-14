"""Single source of truth for the Phase 1 design system."""
from pathlib import Path

TOKENS = {
    "background": "#0B0D14", "sidebar": "#151824", "surface": "#1D2030",
    "violet": "#9164FF", "cyan": "#35D6C1", "text": "#F4F5FA",
    "muted": "#9A9DB3", "border": "#2A2D40", "selected": "#30254C",
}


def stylesheet() -> str:
    result = Path(__file__).with_name("styles.qss").read_text(encoding="utf-8")
    for name, value in TOKENS.items():
        result = result.replace("@" + name, value)
    return result

