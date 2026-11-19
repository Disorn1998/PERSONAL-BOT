"""Design tokens for persona-bot UI (§17.2).

Migrated in Phase 1a from Phase 0 teal stub → warm cream + primary #6A5ACD.
Keep in sync with ``.streamlit/config.toml``.
"""

from __future__ import annotations

from typing import Final

# Colors (§17.2)
COLOR_PRIMARY: Final[str] = "#6A5ACD"
COLOR_BACKGROUND: Final[str] = "#F4F1EA"
COLOR_SECONDARY_BACKGROUND: Final[str] = "#EBE6DC"
COLOR_TEXT: Final[str] = "#1A1D21"
COLOR_MUTED_TEXT: Final[str] = "#5B6570"
COLOR_BORDER: Final[str] = "#D9D2C5"
COLOR_SUCCESS: Final[str] = "#15803D"
COLOR_WARNING: Final[str] = "#B45309"
COLOR_ERROR: Final[str] = "#B91C1C"
COLOR_INFO: Final[str] = "#1D4ED8"

# Typography — Inter (Latin) + Noto Sans Thai from persona_bot/static/fonts/
FONT_FAMILY_UI: Final[str] = '"Inter", "Noto Sans Thai", sans-serif'
FONT_FAMILY_MONO: Final[str] = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
FONT_SIZE_BODY_PX: Final[int] = 16
FONT_SIZE_SMALL_PX: Final[int] = 13
FONT_SIZE_TITLE_PX: Final[int] = 22

# Spacing / radius
SPACE_XS_PX: Final[int] = 4
SPACE_SM_PX: Final[int] = 8
SPACE_MD_PX: Final[int] = 16
SPACE_LG_PX: Final[int] = 24
RADIUS_MD_PX: Final[int] = 8
