"""Inline CSS for chat bubbles / welcome / layout — bundled fonts only (no CDN §17)."""

from __future__ import annotations

from persona_bot.ui import tokens
from persona_bot.ui.fonts import font_face_css


def custom_css() -> str:
    """CSS injected once; uses design tokens + self-hosted ``@font-face``."""
    faces = font_face_css()
    r_lg = tokens.RADIUS_LG_PX
    r_sm = tokens.SPACE_SM_PX
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
  [data-testid="stSidebar"] [data-testid="stExpander"] {{
    border: 1px solid {tokens.COLOR_BORDER};
    border-radius: {tokens.RADIUS_MD_PX}px;
    background: {tokens.COLOR_SECONDARY_BACKGROUND};
    box-shadow: {tokens.SHADOW_SOFT};
    margin-bottom: {tokens.SPACE_SM_PX}px;
  }}
  /* Chat bubbles — soft 3D + consistent rhythm (selector + class markers) */
  div[data-testid="stChatMessage"] {{
    border-radius: {tokens.RADIUS_LG_PX}px;
    padding: 12px {tokens.SPACE_MD_PX}px;
    border: 1px solid {tokens.COLOR_BORDER};
    background: {tokens.COLOR_ASSISTANT_BUBBLE};
    box-shadow: {tokens.SHADOW_SOFT};
    margin-bottom: 12px;
  }}
  div[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {{
    gap: 0;
  }}
  div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
  div[data-testid="stChatMessage"]:has(img[alt="user"]),
  div[data-testid="stChatMessage"]:has(.pb-role-user) {{
    background: {tokens.COLOR_USER_BUBBLE};
    border-color: {tokens.COLOR_PRIMARY_DEEP};
    color: {tokens.COLOR_USER_BUBBLE_TEXT};
    margin-left: 12%;
    border-radius: {r_lg}px {r_lg}px {r_sm}px {r_lg}px;
  }}
  div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) p,
  div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) span,
  div[data-testid="stChatMessage"]:has(img[alt="user"]) p,
  div[data-testid="stChatMessage"]:has(img[alt="user"]) span,
  div[data-testid="stChatMessage"]:has(.pb-role-user) p,
  div[data-testid="stChatMessage"]:has(.pb-role-user) span {{
    color: {tokens.COLOR_USER_BUBBLE_TEXT};
  }}
  div[data-testid="stChatMessage"]:has(.pb-role-assistant),
  div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]),
  div[data-testid="stChatMessage"]:has(img[alt="assistant"]) {{
    background: {tokens.COLOR_ASSISTANT_BUBBLE};
    border-color: {tokens.COLOR_BORDER};
    margin-right: 8%;
    border-radius: {r_lg}px {r_lg}px {r_lg}px {r_sm}px;
  }}
  /* Soft blue circular assistant avatar */
  div[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarAssistant"],
  div[data-testid="stChatMessage"] img[alt="assistant"] {{
    background: {tokens.COLOR_ACCENT_WASH} !important;
    border: 1px solid {tokens.COLOR_ACCENT_SOFT};
    border-radius: 999px;
    box-shadow: none;
  }}
  div[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarUser"],
  div[data-testid="stChatMessage"] img[alt="user"] {{
    background: {tokens.COLOR_PRIMARY_DEEP} !important;
    border-radius: 999px;
  }}
  /* Reliable markdown wrappers (Windows-safe when :has is flaky) */
  .pb-bubble-user,
  .pb-bubble-assistant {{
    background: transparent;
    padding: 0;
    margin: 0;
    font-size: {tokens.FONT_SIZE_BODY_PX}px;
    line-height: {tokens.LINE_HEIGHT_BODY};
    letter-spacing: {tokens.LETTER_SPACING_BODY};
    font-weight: 400;
  }}
  .pb-bubble-user {{
    color: {tokens.COLOR_USER_BUBBLE_TEXT};
    border-radius: {r_lg}px {r_lg}px {r_sm}px {r_lg}px;
  }}
  .pb-bubble-assistant {{
    color: {tokens.COLOR_TEXT};
    border-radius: {r_lg}px {r_lg}px {r_lg}px {r_sm}px;
  }}
  .pb-bubble-assistant p {{
    margin: 0.4em 0;
    line-height: {tokens.LINE_HEIGHT_BODY};
  }}
  .pb-bubble-assistant p:first-child {{
    margin-top: 0;
  }}
  .pb-bubble-assistant p:last-child {{
    margin-bottom: 0;
  }}
  .pb-role-user, .pb-role-assistant {{
    display: none;
  }}
  /* Citation chips — compact, sit in the line without crowding */
  .pb-cite {{
    display: inline;
    padding: 0.05em 0.32em;
    margin: 0 0.12em;
    border-radius: {tokens.RADIUS_SM_PX}px;
    border: 1px solid {tokens.COLOR_ACCENT_SOFT};
    background: {tokens.COLOR_ACCENT_WASH};
    color: {tokens.COLOR_PRIMARY_DEEP};
    font-size: 0.78em;
    font-weight: 500;
    line-height: inherit;
    letter-spacing: 0.01em;
    vertical-align: baseline;
    white-space: nowrap;
    box-shadow: none;
  }}
  /* New-message fade (~180ms) */
  @keyframes pb-fade {{
    from {{ opacity: 0; transform: translateY(4px); }}
    to {{ opacity: 1; transform: translateY(0); }}
  }}
  .pb-fade {{
    animation: pb-fade 180ms ease-out;
  }}
  /* Chat input — large radius, primary focus */
  [data-testid="stChatInput"] {{
    border-radius: {tokens.RADIUS_LG_PX}px !important;
    background: {tokens.COLOR_SECONDARY_BACKGROUND};
    box-shadow: {tokens.SHADOW_SOFT};
  }}
  [data-testid="stChatInput"] textarea,
  [data-testid="stChatInput"] div[contenteditable="true"] {{
    border-radius: {tokens.RADIUS_LG_PX}px !important;
    background: {tokens.COLOR_SECONDARY_BACKGROUND} !important;
  }}
  [data-testid="stChatInput"]:focus-within {{
    border-color: {tokens.COLOR_PRIMARY} !important;
    box-shadow: 0 0 0 2px {tokens.COLOR_ACCENT_WASH}, {tokens.SHADOW_SOFT};
  }}
  /* Privacy caption — muted, not an alert */
  .pb-privacy {{
    margin: 0 0 {tokens.SPACE_SM_PX}px 0;
    padding: 0;
    color: {tokens.COLOR_MUTED_TEXT};
    font-size: {tokens.FONT_SIZE_META_PX}px;
    line-height: {tokens.LINE_HEIGHT_META};
    letter-spacing: {tokens.LETTER_SPACING_META};
    font-weight: 400;
    opacity: 0.9;
  }}
  .pb-privacy-wrap {{
    margin: 0 0 {tokens.SPACE_MD_PX}px 0;
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
  /* Soft 2D float + tilt/parallax (CSS only — no WebGL / .glb) */
  @keyframes pb-welcome-float {{
    0%, 100% {{
      transform: translateY(0) translateX(0) rotate(0deg);
    }}
    40% {{
      transform: translateY(-10px) translateX(3px) rotate(-0.6deg);
    }}
    70% {{
      transform: translateY(-4px) translateX(-2px) rotate(0.4deg);
    }}
  }}
  @keyframes pb-welcome-shadow-pulse {{
    0%, 100% {{
      box-shadow: {tokens.SHADOW_SOFT};
    }}
    50% {{
      box-shadow: 0 18px 40px rgba(37, 99, 235, 0.18);
    }}
  }}
  .pb-welcome-hero {{
    width: 100%;
    margin: {tokens.SPACE_MD_PX}px 0 {tokens.SPACE_LG_PX}px 0;
    padding: 6px 2px 14px 2px;
    animation: pb-welcome-shadow-pulse 5s ease-in-out infinite;
  }}
  .pb-welcome-hero img {{
    width: 100%;
    display: block;
    border-radius: {tokens.RADIUS_LG_PX}px;
    transform-origin: center center;
    will-change: transform;
    box-shadow: {tokens.SHADOW_SOFT};
    animation: pb-welcome-float 5s ease-in-out infinite;
  }}
  @media (prefers-reduced-motion: reduce) {{
    .pb-welcome-hero,
    .pb-welcome-hero img {{
      animation: none;
      transform: none;
      will-change: auto;
    }}
  }}
  .pb-path-row {{
    display: flex;
    flex-wrap: wrap;
    gap: {tokens.SPACE_MD_PX}px;
    margin: {tokens.SPACE_MD_PX}px 0;
  }}
  /* Knowledge file list — soft panel inside sidebar expander */
  .pb-knowledge-files {{
    margin: {tokens.SPACE_SM_PX}px 0 {tokens.SPACE_MD_PX}px 0;
    padding: {tokens.SPACE_SM_PX}px {tokens.SPACE_MD_PX}px;
    border: 1px solid {tokens.COLOR_BORDER};
    border-radius: {tokens.RADIUS_MD_PX}px;
    background: {tokens.COLOR_ACCENT_WASH};
    box-shadow: {tokens.SHADOW_SOFT};
  }}
  .pb-knowledge-files-title {{
    margin: 0;
    color: {tokens.COLOR_PRIMARY_DEEP};
    font-size: {tokens.FONT_SIZE_SMALL_PX}px;
    font-weight: 600;
    letter-spacing: {tokens.LETTER_SPACING_META};
  }}
  .pb-empty {{
    text-align: center;
    padding: {tokens.SPACE_LG_PX}px {tokens.SPACE_MD_PX}px;
    color: {tokens.COLOR_MUTED_TEXT};
  }}
  .pb-empty p {{
    margin: 0;
    font-size: {tokens.FONT_SIZE_BODY_PX}px;
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
    padding: 10px;
    border-radius: 999px;
    background: {tokens.COLOR_ACCENT_WASH};
    border: 1px solid {tokens.COLOR_ACCENT_SOFT};
    box-shadow: {tokens.SHADOW_SOFT};
  }}
  /* Meta row — calm, separated from body (not stuck to last line) */
  .pb-meta {{
    display: flex;
    flex-wrap: wrap;
    gap: {tokens.SPACE_XS_PX}px {tokens.SPACE_SM_PX}px;
    align-items: center;
    margin-top: 10px;
    padding-top: {tokens.SPACE_SM_PX}px;
    border-top: 1px solid {tokens.COLOR_BORDER};
    color: {tokens.COLOR_MUTED_TEXT};
    font-size: {tokens.FONT_SIZE_META_PX}px;
    line-height: {tokens.LINE_HEIGHT_META};
    letter-spacing: {tokens.LETTER_SPACING_META};
    font-weight: 400;
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
    font-size: {tokens.FONT_SIZE_META_PX}px;
    margin-top: {tokens.SPACE_SM_PX}px;
  }}
  .pb-badge {{
    display: inline-block;
    border: 1px solid {tokens.COLOR_BORDER};
    border-radius: {tokens.RADIUS_SM_PX}px;
    padding: 1px 8px;
    font-size: {tokens.FONT_SIZE_META_PX}px;
    line-height: {tokens.LINE_HEIGHT_META};
    letter-spacing: {tokens.LETTER_SPACING_META};
    font-weight: 500;
    color: {tokens.COLOR_MUTED_TEXT};
    background: transparent;
    box-shadow: none;
  }}
  .pb-badge.fallback {{
    border-color: {tokens.COLOR_WARNING};
    color: {tokens.COLOR_WARNING};
    background: transparent;
  }}
  .pb-badge.knowledge {{
    border-color: {tokens.COLOR_ACCENT_SOFT};
    color: {tokens.COLOR_PRIMARY_DEEP};
    background: {tokens.COLOR_ACCENT_WASH};
    font-weight: 500;
  }}
  /* Daily usage energy bar — under model · tokens meta */
  .pb-energy {{
    margin-top: 6px;
    width: 100%;
    max-width: 240px;
  }}
  .pb-energy-caption {{
    margin: 0 0 {tokens.SPACE_XS_PX}px 0;
    padding: 0;
    color: {tokens.COLOR_MUTED_TEXT};
    font-size: {tokens.FONT_SIZE_META_PX}px;
    line-height: {tokens.LINE_HEIGHT_META};
    letter-spacing: {tokens.LETTER_SPACING_META};
    font-weight: 400;
  }}
  .pb-energy-track {{
    height: 6px;
    border-radius: 999px;
    background: {tokens.COLOR_ACCENT_WASH};
    border: 1px solid {tokens.COLOR_BORDER};
    overflow: hidden;
  }}
  .pb-energy-fill {{
    height: 100%;
    border-radius: 999px;
    box-shadow: none;
  }}
  .pb-energy-fill.green {{ background: {tokens.COLOR_ENERGY_GREEN}; }}
  .pb-energy-fill.yellow {{ background: {tokens.COLOR_ENERGY_YELLOW}; }}
  .pb-energy-fill.orange {{ background: {tokens.COLOR_ENERGY_ORANGE}; }}
  .pb-energy-fill.red {{ background: {tokens.COLOR_ENERGY_RED}; }}
  .pb-energy-unset {{
    margin: 6px 0 0 0;
    padding: 0;
    color: {tokens.COLOR_MUTED_TEXT};
    font-size: {tokens.FONT_SIZE_META_PX}px;
    line-height: {tokens.LINE_HEIGHT_META};
    letter-spacing: {tokens.LETTER_SPACING_META};
    font-weight: 400;
    opacity: 0.85;
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
  /* Primary / secondary buttons — soft lift */
  div.stButton > button[kind="primary"],
  div.stButton > button[data-testid="baseButton-primary"] {{
    border-radius: {tokens.RADIUS_MD_PX}px;
    box-shadow: {tokens.SHADOW_SOFT};
  }}
  div.stButton > button {{
    border-radius: {tokens.RADIUS_MD_PX}px;
  }}
  /* Info / success banners — wash + primary */
  div[data-testid="stAlert"] {{
    border-radius: {tokens.RADIUS_MD_PX}px;
    box-shadow: {tokens.SHADOW_SOFT};
  }}
  div[data-testid="stAlert"][kind="info"],
  div[data-testid="stNotification"] {{
    border-color: {tokens.COLOR_ACCENT_SOFT};
  }}
  /* Keep primary column usable ~360px */
  .block-container {{
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 880px;
  }}
  /* Guided tour — coach card + soft spotlight (CSS only, no WebGL) */
  .pb-tour-anchor {{
    height: 0;
    margin: 0;
    padding: 0;
    overflow: hidden;
  }}
  .pb-tour-coach {{
    border: 1px solid {tokens.COLOR_ACCENT_SOFT};
    border-radius: {tokens.RADIUS_LG_PX}px;
    padding: {tokens.SPACE_MD_PX}px;
    margin: 0 0 {tokens.SPACE_MD_PX}px 0;
    background: linear-gradient(
      180deg, {tokens.COLOR_ACCENT_WASH} 0%, {tokens.COLOR_SECONDARY_BACKGROUND} 70%);
    box-shadow: {tokens.SHADOW_SOFT};
  }}
  .pb-tour-coach-row {{
    display: flex;
    align-items: flex-start;
    gap: {tokens.SPACE_MD_PX}px;
  }}
  .pb-tour-mascot {{
    flex: 0 0 auto;
    width: 56px;
    height: 56px;
    border-radius: 999px;
    border: 1px solid {tokens.COLOR_ACCENT_SOFT};
    background: {tokens.COLOR_SECONDARY_BACKGROUND};
    box-shadow: {tokens.SHADOW_SOFT};
    object-fit: cover;
  }}
  .pb-tour-coach-copy {{
    flex: 1 1 auto;
    min-width: 0;
  }}
  .pb-tour-progress {{
    margin: 0 0 4px 0;
    color: {tokens.COLOR_PRIMARY_DEEP};
    font-size: {tokens.FONT_SIZE_SMALL_PX}px;
    font-weight: 600;
  }}
  .pb-tour-body {{
    margin: 0;
    color: {tokens.COLOR_TEXT};
    font-size: {tokens.FONT_SIZE_BODY_PX}px;
    line-height: 1.45;
  }}
  /* Soft spotlight rings for the active tour target */
  body:has(.pb-tour-coach[data-tour-step="welcome"]) .pb-welcome,
  body:has(.pb-tour-coach[data-tour-step="path"]) .pb-welcome {{
    outline: 3px solid {tokens.COLOR_PRIMARY};
    outline-offset: 4px;
    box-shadow: 0 0 0 8px rgba(37, 99, 235, 0.12), {tokens.SHADOW_SOFT};
  }}
  body:has(.pb-tour-coach[data-tour-step="persona"])
    [data-testid="stSidebar"] [data-testid="stSelectbox"]:first-of-type {{
    outline: 3px solid {tokens.COLOR_PRIMARY};
    outline-offset: 4px;
    border-radius: {tokens.RADIUS_MD_PX}px;
    box-shadow: 0 0 0 8px rgba(37, 99, 235, 0.12);
  }}
  body:has(.pb-tour-coach[data-tour-step="knowledge"]) .pb-tour-spot-knowledge {{
    min-height: 8px;
    margin-bottom: 6px;
    border-radius: {tokens.RADIUS_MD_PX}px;
    outline: 3px solid {tokens.COLOR_PRIMARY};
    outline-offset: 4px;
    box-shadow: 0 0 0 8px rgba(37, 99, 235, 0.12);
  }}
  body:has(.pb-tour-coach[data-tour-step="knowledge"])
    [data-testid="stSidebar"] [data-testid="stExpander"][aria-expanded="true"] {{
    outline: 3px solid {tokens.COLOR_PRIMARY};
    outline-offset: 3px;
    box-shadow: 0 0 0 6px rgba(37, 99, 235, 0.12);
  }}
  body:has(.pb-tour-coach[data-tour-step="chat"]) [data-testid="stChatInput"] {{
    outline: 3px solid {tokens.COLOR_PRIMARY};
    outline-offset: 4px;
    box-shadow: 0 0 0 8px rgba(37, 99, 235, 0.12), {tokens.SHADOW_SOFT};
  }}
  body:has(.pb-tour-coach[data-tour-step="path"])
    div.stButton > button[kind="primary"],
  body:has(.pb-tour-coach[data-tour-step="path"])
    div.stButton > button[data-testid="baseButton-primary"] {{
    outline: 3px solid {tokens.COLOR_PRIMARY};
    outline-offset: 3px;
    box-shadow: 0 0 0 6px rgba(37, 99, 235, 0.14), {tokens.SHADOW_SOFT};
  }}
  @media (prefers-reduced-motion: reduce) {{
    .pb-tour-coach {{
      transition: none;
    }}
  }}
  @media (max-width: 400px) {{
    .block-container {{
      padding-left: 0.6rem;
      padding-right: 0.6rem;
    }}
    .pb-welcome-brand {{
      font-size: 28px;
    }}
    .pb-tour-mascot {{
      width: 44px;
      height: 44px;
    }}
    div[data-testid="stChatMessage"]:has(.pb-role-user),
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
      margin-left: 4%;
    }}
    div[data-testid="stChatMessage"]:has(.pb-role-assistant) {{
      margin-right: 2%;
    }}
  }}
</style>
"""
