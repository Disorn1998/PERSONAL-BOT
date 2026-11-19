"""Bundled OFL UI fonts — present on disk and injectable into CSS."""

from __future__ import annotations

from persona_bot.ui.fonts import bundled_font_files, font_face_css, fonts_dir
from persona_bot.ui.theme import custom_css
from persona_bot.ui.tokens import FONT_FAMILY_UI


def test_bundled_font_files_exist() -> None:
    assert fonts_dir().is_dir()
    missing = [p.name for p in bundled_font_files() if not p.is_file()]
    assert not missing, f"missing font binaries: {missing}"
    for licence in ("OFL-Inter.txt", "OFL-NotoSansThai.txt"):
        path = fonts_dir() / licence
        assert path.is_file(), licence
        text = path.read_text(encoding="utf-8")
        assert "SIL OPEN FONT LICENSE" in text.upper()


def test_font_face_css_embeds_woff2_data_uris() -> None:
    css = font_face_css()
    assert "@font-face" in css
    assert "font/woff2;base64," in css
    assert 'font-family: "Inter"' in css
    assert 'font-family: "Noto Sans Thai"' in css
    assert "Inter" in FONT_FAMILY_UI and "Noto Sans Thai" in FONT_FAMILY_UI
    theme = custom_css()
    assert "font/woff2;base64," in theme
    assert FONT_FAMILY_UI.split(",")[0].strip('"') in theme or "Inter" in theme
    assert "@keyframes pb-fade" in theme
    assert "@keyframes pb-welcome-float" in theme
    assert "@keyframes pb-welcome-shadow-pulse" in theme
    assert "prefers-reduced-motion" in theme
    assert "pb-welcome-hero" in theme
    assert "pb-cite" in theme
    assert "pb-role-user" in theme
    assert "pb-privacy" in theme
    assert "pb-energy" in theme
    assert "pb-energy-fill" in theme
    assert "pb-knowledge-files" in theme
    assert "pb-rules-panel" in theme
    assert "line-height: 1.55" in theme
    assert '[data-testid="stChatInput"]' in theme
