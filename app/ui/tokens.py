"""Design tokens for persona-bot UI (Phase 0).

Keep in sync with ``.streamlit/config.toml``. Full §17.2 tables from the owner
message supersede these values when they differ — see docs/ASSUMPTIONS.md.
"""

from __future__ import annotations

from typing import Final

# Colors (light theme)
COLOR_PRIMARY: Final[str] = "#0F766E"
COLOR_BACKGROUND: Final[str] = "#F7F8FA"
COLOR_SECONDARY_BACKGROUND: Final[str] = "#EEF1F4"
COLOR_TEXT: Final[str] = "#1A1D21"
COLOR_MUTED_TEXT: Final[str] = "#5B6570"
COLOR_BORDER: Final[str] = "#D5DCE3"
COLOR_SUCCESS: Final[str] = "#15803D"
COLOR_WARNING: Final[str] = "#B45309"
COLOR_ERROR: Final[str] = "#B91C1C"
COLOR_INFO: Final[str] = "#1D4ED8"

# Typography
FONT_FAMILY_UI: Final[str] = "sans-serif"
FONT_FAMILY_MONO: Final[str] = "monospace"
FONT_SIZE_BODY_PX: Final[int] = 16
FONT_SIZE_SMALL_PX: Final[int] = 13
FONT_SIZE_TITLE_PX: Final[int] = 22

# Spacing / radius
SPACE_XS_PX: Final[int] = 4
SPACE_SM_PX: Final[int] = 8
SPACE_MD_PX: Final[int] = 16
SPACE_LG_PX: Final[int] = 24
RADIUS_MD_PX: Final[int] = 8
