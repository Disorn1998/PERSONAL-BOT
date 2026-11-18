"""Inline CSS for chat bubbles / layout — no external fonts or scripts (§17)."""

from __future__ import annotations

from app.ui import tokens


def custom_css() -> str:
    """CSS injected once; uses design tokens only."""
    return f"""
<style>
  .stApp {{
    background: {tokens.COLOR_BACKGROUND};
  }}
  [data-testid="stSidebar"] {{
    background: {tokens.COLOR_SECONDARY_BACKGROUND};
    border-right: 1px solid {tokens.COLOR_BORDER};
  }}
  div[data-testid="stChatMessage"] {{
    border-radius: {tokens.RADIUS_MD_PX}px;
    padding: {tokens.SPACE_SM_PX}px {tokens.SPACE_MD_PX}px;
  }}
  .pb-welcome {{
    border: 1px solid {tokens.COLOR_BORDER};
    border-radius: {tokens.RADIUS_MD_PX}px;
    padding: {tokens.SPACE_LG_PX}px;
    background: {tokens.COLOR_SECONDARY_BACKGROUND};
    margin-bottom: {tokens.SPACE_MD_PX}px;
  }}
  .pb-welcome h1 {{
    color: {tokens.COLOR_PRIMARY};
    font-size: {tokens.FONT_SIZE_TITLE_PX}px;
    margin: 0 0 {tokens.SPACE_SM_PX}px 0;
  }}
  .pb-meta {{
    color: {tokens.COLOR_MUTED_TEXT};
    font-size: {tokens.FONT_SIZE_SMALL_PX}px;
  }}
  .pb-error {{
    border-left: 4px solid {tokens.COLOR_ERROR};
    background: {tokens.COLOR_SECONDARY_BACKGROUND};
    padding: {tokens.SPACE_MD_PX}px;
    border-radius: {tokens.RADIUS_MD_PX}px;
    margin: {tokens.SPACE_SM_PX}px 0;
  }}
  .pb-error .hint {{
    color: {tokens.COLOR_MUTED_TEXT};
    font-size: {tokens.FONT_SIZE_SMALL_PX}px;
    margin-top: {tokens.SPACE_SM_PX}px;
  }}
  .pb-badge {{
    display: inline-block;
    border: 1px solid {tokens.COLOR_BORDER};
    border-radius: {tokens.RADIUS_MD_PX}px;
    padding: 2px 8px;
    font-size: {tokens.FONT_SIZE_SMALL_PX}px;
    color: {tokens.COLOR_MUTED_TEXT};
    margin-right: 6px;
  }}
  .pb-badge.fallback {{
    border-color: {tokens.COLOR_WARNING};
    color: {tokens.COLOR_WARNING};
  }}
  /* Keep primary column usable ~360px */
  .block-container {{
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 880px;
  }}
  @media (max-width: 400px) {{
    .block-container {{
      padding-left: 0.6rem;
      padding-right: 0.6rem;
    }}
  }}
</style>
"""
