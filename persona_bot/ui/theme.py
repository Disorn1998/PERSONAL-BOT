"""Inline CSS for chat bubbles / welcome / layout — bundled fonts only (no CDN §17)."""

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
    background:
      radial-gradient(1200px 600px at 10% -10%, {tokens.COLOR_ACCENT_WASH} 0%, transparent 55%),
      radial-gradient(900px 500px at 100% 0%, #EFF6FF 0%, transparent 50%),
      {tokens.COLOR_BACKGROUND};
  }}
  [data-testid="stSidebar"] {{
    background: {tokens.COLOR_SECONDARY_BACKGROUND};
    border-right: 1px solid {tokens.COLOR_BORDER};
    box-shadow: {tokens.SHADOW_SOFT};
  }}
  /* Chat bubbles — soft 3D */
  div[data-testid="stChatMessage"] {{
    border-radius: {tokens.RADIUS_LG_PX}px;
    padding: {tokens.SPACE_SM_PX}px {tokens.SPACE_MD_PX}px;
    border: 1px solid {tokens.COLOR_BORDER};
    background: {tokens.COLOR_ASSISTANT_BUBBLE};
    box-shadow: {tokens.SHADOW_SOFT};
    margin-bottom: {tokens.SPACE_SM_PX}px;
  }}
  div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
  div[data-testid="stChatMessage"]:has(img[alt="user"]) {{
    background: {tokens.COLOR_USER_BUBBLE};
    border-color: {tokens.COLOR_PRIMARY_DEEP};
    color: {tokens.COLOR_USER_BUBBLE_TEXT};
  }}
  div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) p,
  div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) span,
  div[data-testid="stChatMessage"]:has(img[alt="user"]) p,
  div[data-testid="stChatMessage"]:has(img[alt="user"]) span {{
    color: {tokens.COLOR_USER_BUBBLE_TEXT};
  }}
  /* Fallback class toggled via markdown wrapper */
  .pb-bubble-user {{
    background: {tokens.COLOR_USER_BUBBLE};
    color: {tokens.COLOR_USER_BUBBLE_TEXT};
    border-radius: {tokens.RADIUS_LG_PX}px;
    padding: {tokens.SPACE_MD_PX}px;
    box-shadow: {tokens.SHADOW_SOFT};
  }}
  .pb-bubble-assistant {{
    background: {tokens.COLOR_ASSISTANT_BUBBLE};
    color: {tokens.COLOR_TEXT};
    border: 1px solid {tokens.COLOR_BORDER};
    border-radius: {tokens.RADIUS_LG_PX}px;
    padding: {tokens.SPACE_MD_PX}px;
    box-shadow: {tokens.SHADOW_SOFT};
  }}
  .pb-welcome {{
    border: 1px solid {tokens.COLOR_BORDER};
    border-radius: {tokens.RADIUS_LG_PX}px;
    padding: {tokens.SPACE_LG_PX}px;
    background: {tokens.COLOR_SECONDARY_BACKGROUND};
    margin-bottom: {tokens.SPACE_MD_PX}px;
    box-shadow: {tokens.SHADOW_SOFT};
  }}
  .pb-welcome-brand {{
    color: {tokens.COLOR_PRIMARY};
    font-size: {tokens.FONT_SIZE_HERO_PX}px;
    font-weight: 600;
    line-height: 1.15;
    margin: 0 0 {tokens.SPACE_SM_PX}px 0;
    letter-spacing: -0.02em;
  }}
  .pb-welcome h1 {{
    color: {tokens.COLOR_PRIMARY};
    font-size: {tokens.FONT_SIZE_TITLE_PX}px;
    margin: 0 0 {tokens.SPACE_SM_PX}px 0;
  }}
  .pb-welcome-sub {{
    color: {tokens.COLOR_MUTED_TEXT};
    font-size: {tokens.FONT_SIZE_BODY_PX}px;
    margin: 0 0 {tokens.SPACE_MD_PX}px 0;
  }}
  .pb-welcome-hero {{
    width: 100%;
    border-radius: {tokens.RADIUS_LG_PX}px;
    overflow: hidden;
    margin: {tokens.SPACE_MD_PX}px 0;
    box-shadow: {tokens.SHADOW_SOFT};
  }}
  .pb-welcome-hero img {{
    width: 100%;
    display: block;
  }}
  .pb-path-row {{
    display: flex;
    flex-wrap: wrap;
    gap: {tokens.SPACE_MD_PX}px;
    margin: {tokens.SPACE_MD_PX}px 0;
  }}
  .pb-empty {{
    text-align: center;
    padding: {tokens.SPACE_LG_PX}px {tokens.SPACE_MD_PX}px;
    color: {tokens.COLOR_MUTED_TEXT};
  }}
  .pb-empty-icons {{
    display: flex;
    justify-content: center;
    gap: {tokens.SPACE_MD_PX}px;
    margin-bottom: {tokens.SPACE_MD_PX}px;
  }}
  .pb-empty-icons img {{
    width: 48px;
    height: 48px;
  }}
  .pb-meta {{
    color: {tokens.COLOR_MUTED_TEXT};
    font-size: {tokens.FONT_SIZE_SMALL_PX}px;
  }}
  .pb-error {{
    border-left: 4px solid {tokens.COLOR_ERROR};
    background: {tokens.COLOR_ACCENT_WASH};
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
    padding: 2px 10px;
    font-size: {tokens.FONT_SIZE_SMALL_PX}px;
    color: {tokens.COLOR_MUTED_TEXT};
    margin-right: 6px;
    background: {tokens.COLOR_SECONDARY_BACKGROUND};
  }}
  .pb-badge.fallback {{
    border-color: {tokens.COLOR_WARNING};
    color: {tokens.COLOR_WARNING};
  }}
  .pb-badge.knowledge {{
    border-color: {tokens.COLOR_ACCENT_SOFT};
    color: {tokens.COLOR_PRIMARY_DEEP};
    background: {tokens.COLOR_ACCENT_WASH};
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
    background: {tokens.COLOR_ACCENT_WASH};
  }}
  .pb-wizard-step.done {{
    border-color: {tokens.COLOR_SUCCESS};
    color: {tokens.COLOR_SUCCESS};
  }}
  /* Primary buttons — soft lift */
  div.stButton > button[kind="primary"],
  div.stButton > button[data-testid="baseButton-primary"] {{
    border-radius: {tokens.RADIUS_MD_PX}px;
    box-shadow: {tokens.SHADOW_SOFT};
  }}
  div.stButton > button {{
    border-radius: {tokens.RADIUS_MD_PX}px;
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
    .pb-welcome-brand {{
      font-size: 28px;
    }}
  }}
</style>
"""
