"""Local illustration paths (no CDN)."""

from __future__ import annotations

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


def icon_path(name: str) -> Path:
    """Return path to a local SVG icon (``name`` without extension)."""
    return _ICONS / f"{name}.svg"
