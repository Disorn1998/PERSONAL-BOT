"""Load bundled OFL UI fonts for inline Streamlit CSS (no CDN)."""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

_FONTS_DIR = Path(__file__).resolve().parents[1] / "static" / "fonts"

# (css_family, relative filename, weight, style)
_FONT_FACES: tuple[tuple[str, str, int, str], ...] = (
    ("Inter", "Inter-Regular.woff2", 400, "normal"),
    ("Inter", "Inter-SemiBold.woff2", 600, "normal"),
    ("Noto Sans Thai", "NotoSansThai-Regular.woff2", 400, "normal"),
    ("Noto Sans Thai", "NotoSansThai-Bold.woff2", 700, "normal"),
)


def fonts_dir() -> Path:
    return _FONTS_DIR


@lru_cache(maxsize=1)
def font_face_css() -> str:
    """Return ``@font-face`` rules with base64 ``data:`` URLs for bundled woff2."""
    blocks: list[str] = []
    for family, filename, weight, style in _FONT_FACES:
        path = _FONTS_DIR / filename
        if not path.is_file():
            continue
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
        blocks.append(
            f"""@font-face {{
  font-family: "{family}";
  font-style: {style};
  font-weight: {weight};
  font-display: swap;
  src: url(data:font/woff2;base64,{payload}) format("woff2");
}}"""
        )
    return "\n".join(blocks)


def bundled_font_files() -> list[Path]:
    """Paths of expected binary font files (for packaging / smoke checks)."""
    return [_FONTS_DIR / name for _, name, _, _ in _FONT_FACES]
