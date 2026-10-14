"""Single source of truth for the Phase 1 design system."""
from pathlib import Path

TOKENS = {
    "background": "#F8D9E0", "sidebar": "#FFFFFF", "surface": "#FF9FBD",
    "violet": "#F16B99", "cyan": "#B82560", "text": "#171318",
    "muted": "#70515D", "border": "#20181D", "selected": "#FFC0D2",
}


def stylesheet() -> str:
    result = Path(__file__).with_name("styles.qss").read_text(encoding="utf-8")
    for name, value in TOKENS.items():
        result = result.replace("@" + name, value)
    return result

