"""Inline CSS for chat bubbles / layout — bundled OFL fonts only (no CDN §17)."""

from __future__ import annotations

from persona_bot.ui import tokens
from persona_bot.ui.fonts import font_face_css


def custom_css() -> str:
    """CSS injected once; uses design tokens + self-hosted ``@font-face``."""
    faces = font_face_css()
    return f"""
<style>
{faces}
  html, body, .stApp, [data-testid="stSidebar"], .pb-welcome, .pb-meta, .pb-error {{
    font-family: {tokens.FONT_FAMILY_UI};
  }}
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
  .pb-wizard {{
    display: flex;
    flex-wrap: wrap;
    gap: {tokens.SPACE_SM_PX}px;
    margin: {tokens.SPACE_SM_PX}px 0 {tokens.SPACE_MD_PX}px 0;
  }}
  .pb-wizard-step {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border: 1px solid {tokens.COLOR_BORDER};
    border-radius: {tokens.RADIUS_MD_PX}px;
    padding: 4px 10px;
    font-size: {tokens.FONT_SIZE_SMALL_PX}px;
    color: {tokens.COLOR_MUTED_TEXT};
    background: {tokens.COLOR_BACKGROUND};
  }}
  .pb-wizard-step .n {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 1.4em;
    font-weight: 600;
  }}
  .pb-wizard-step.active {{
    border-color: {tokens.COLOR_PRIMARY};
    color: {tokens.COLOR_TEXT};
    background: {tokens.COLOR_SECONDARY_BACKGROUND};
  }}
  .pb-wizard-step.done {{
    border-color: {tokens.COLOR_SUCCESS};
    color: {tokens.COLOR_SUCCESS};
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
