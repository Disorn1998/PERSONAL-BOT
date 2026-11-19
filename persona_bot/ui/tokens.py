"""Design tokens for persona-bot UI (§17.2).

Electric blue soft-3D palette (welcome redesign). Keep in sync with
``.streamlit/config.toml``.
"""

from __future__ import annotations

from typing import Final

# Colors — electric blue soft-3D
COLOR_PRIMARY: Final[str] = "#2563EB"
COLOR_PRIMARY_DEEP: Final[str] = "#1D4ED8"
COLOR_BACKGROUND: Final[str] = "#F7FAFF"
COLOR_SECONDARY_BACKGROUND: Final[str] = "#FFFFFF"
COLOR_ACCENT_SOFT: Final[str] = "#93C5FD"
COLOR_ACCENT_WASH: Final[str] = "#DBEAFE"
COLOR_TEXT: Final[str] = "#0F172A"
COLOR_MUTED_TEXT: Final[str] = "#64748B"
COLOR_BORDER: Final[str] = "#E2E8F0"
COLOR_SUCCESS: Final[str] = "#15803D"
COLOR_WARNING: Final[str] = "#B45309"
COLOR_ERROR: Final[str] = "#B91C1C"
COLOR_INFO: Final[str] = "#1D4ED8"
COLOR_ENERGY_GREEN: Final[str] = "#16A34A"
COLOR_ENERGY_YELLOW: Final[str] = "#CA8A04"
COLOR_ENERGY_ORANGE: Final[str] = "#EA580C"
COLOR_ENERGY_RED: Final[str] = "#DC2626"
COLOR_USER_BUBBLE: Final[str] = "#2563EB"
COLOR_USER_BUBBLE_TEXT: Final[str] = "#FFFFFF"
COLOR_ASSISTANT_BUBBLE: Final[str] = "#FFFFFF"

# Typography — Inter (Latin) + Noto Sans Thai from persona_bot/static/fonts/
FONT_FAMILY_UI: Final[str] = '"Inter", "Noto Sans Thai", sans-serif'
FONT_FAMILY_MONO: Final[str] = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
FONT_SIZE_BODY_PX: Final[int] = 16
FONT_SIZE_SMALL_PX: Final[int] = 13
FONT_SIZE_META_PX: Final[int] = 12
FONT_SIZE_TITLE_PX: Final[int] = 28
FONT_SIZE_HERO_PX: Final[int] = 36
LINE_HEIGHT_BODY: Final[float] = 1.55
LINE_HEIGHT_META: Final[float] = 1.4
LETTER_SPACING_BODY: Final[str] = "0.005em"
LETTER_SPACING_META: Final[str] = "0.02em"

# Spacing / radius / shadow
SPACE_XS_PX: Final[int] = 4
SPACE_SM_PX: Final[int] = 8
SPACE_MD_PX: Final[int] = 16
SPACE_LG_PX: Final[int] = 24
RADIUS_SM_PX: Final[int] = 8
RADIUS_MD_PX: Final[int] = 16
RADIUS_LG_PX: Final[int] = 24
SHADOW_SOFT: Final[str] = "0 8px 24px rgba(37, 99, 235, 0.08)"
