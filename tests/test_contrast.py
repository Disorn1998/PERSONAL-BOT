"""UI contrast smoke — F23 automated check against §17.2 tokens."""

from __future__ import annotations

from app.ui import tokens


def _hex_to_rgb(value: str) -> tuple[float, float, float]:
    h = value.removeprefix("#")
    return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)


def _channel(c: float) -> float:
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    r, g, b = _hex_to_rgb(hex_color)
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(fg: str, bg: str) -> float:
    l1 = relative_luminance(fg)
    l2 = relative_luminance(bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def test_body_text_contrast_wcag_aa() -> None:
    ratio = contrast_ratio(tokens.COLOR_TEXT, tokens.COLOR_BACKGROUND)
    assert ratio >= 4.5, f"body text contrast {ratio:.2f} < 4.5"


def test_muted_text_contrast_reasonable() -> None:
    ratio = contrast_ratio(tokens.COLOR_MUTED_TEXT, tokens.COLOR_BACKGROUND)
    assert ratio >= 3.0, f"muted text contrast {ratio:.2f} < 3.0"


def test_error_on_background_readable() -> None:
    ratio = contrast_ratio(tokens.COLOR_ERROR, tokens.COLOR_BACKGROUND)
    assert ratio >= 3.0, f"error contrast {ratio:.2f} < 3.0"


def test_primary_on_background_visible() -> None:
    # Large UI / brand accent — AA large-text floor.
    ratio = contrast_ratio(tokens.COLOR_PRIMARY, tokens.COLOR_BACKGROUND)
    assert ratio >= 3.0, f"primary contrast {ratio:.2f} < 3.0"
