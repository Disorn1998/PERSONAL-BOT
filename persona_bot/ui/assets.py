"""Local illustration paths (no CDN)."""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

_STATIC = Path(__file__).resolve().parents[1] / "static"
_ILLUSTRATIONS = _STATIC / "illustrations"
_ICONS = _ILLUSTRATIONS / "icons"

WELCOME_HERO_NAME = "welcome-hero.jpg"


def illustrations_dir() -> Path:
    return _ILLUSTRATIONS


def icons_dir() -> Path:
    return _ICONS


def welcome_hero_path() -> Path:
    return _ILLUSTRATIONS / WELCOME_HERO_NAME


@lru_cache(maxsize=1)
def welcome_hero_data_uri() -> str | None:
    """JPEG data URI for the welcome hero (inline HTML / CSS class targeting)."""
    path = welcome_hero_path()
    if not path.is_file():
        return None
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{payload}"


def icon_path(name: str) -> Path:
    """Return path to a local SVG icon (``name`` without extension)."""
    return _ICONS / f"{name}.svg"
