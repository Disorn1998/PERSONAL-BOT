"""Extractive knowledge-only answers (no online LLM).

Used when the Groq key is missing, quota is exhausted, or the network fails.
Retrieves local Chroma hits and formats a templated Thai/EN reply with citations.
Does **not** claim generative ChatGPT-quality offline answers.
"""

from __future__ import annotations

from typing import Any, Literal

from persona_bot.errors import (
    LlmTransportError,
    MissingApiKeyError,
    MissingModelConfigError,
    RateLimitDayError,
    RateLimitMinuteError,
)

Locale = Literal["th", "en"]

KNOWLEDGE_ONLY_BADGE_TH = "ตอบจากคลังความรู้ (ไม่ใช้ AI ออนไลน์)"
KNOWLEDGE_ONLY_BADGE_EN = "Answer from your knowledge (no online AI)"

_EXCERPT_MAX = 480


def filter_passing_chunks(
    chunks: list[dict[str, Any]],
    *,
    min_score: float,
) -> list[dict[str, Any]]:
    """Keep chunks that meet ``min_score`` (same gate as prompt builder)."""
    return [c for c in chunks if float(c.get("score", 0.0)) >= float(min_score)]


def should_fallback_to_knowledge_only(exc: BaseException) -> bool:
    """True for missing key/models, rate limits, or transport failures."""
    return isinstance(
        exc,
        (
            MissingApiKeyError,
            MissingModelConfigError,
            RateLimitDayError,
            RateLimitMinuteError,
            LlmTransportError,
        ),
    )


def knowledge_only_badge(*, locale: str = "th") -> str:
    if locale == "en":
        return KNOWLEDGE_ONLY_BADGE_EN
    return KNOWLEDGE_ONLY_BADGE_TH


def knowledge_only_empty_reply(*, locale: str = "th") -> str:
    """Calm empty state when the index has no passing hits."""
    if locale == "en":
        return (
            "No matching notes found in your knowledge.\n\n"
            "Add or paste notes, make sure the index is Ready, then ask again. "
            "This mode only quotes your files — it does not invent answers."
        )
    return (
        "ไม่พบข้อความที่เกี่ยวข้องในคลังความรู้ของคุณ\n\n"
        "ลองเพิ่มหรือวางโน้ต แล้วตรวจว่าสถานะดัชนีเป็น「พร้อมแล้ว」ก่อนถามอีกครั้ง "
        "โหมดนี้จะอ้างจากไฟล์ของคุณเท่านั้น — ไม่แต่งคำตอบ"
    )


def _trim_excerpt(text: str, *, limit: int = _EXCERPT_MAX) -> str:
    cleaned = " ".join(str(text or "").strip().split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def format_knowledge_only_answer(
    chunks: list[dict[str, Any]],
    *,
    locale: str = "th",
    question: str | None = None,
) -> str:
    """Build a labeled extractive answer from retrieved chunks (no LLM)."""
    badge = knowledge_only_badge(locale=locale)
    if not chunks:
        return knowledge_only_empty_reply(locale=locale)

    lines: list[str] = [f"**{badge}**", ""]
    if locale == "en":
        lines.append(
            "Here are the closest passages from your knowledge. "
            "This is a quote-style answer, not an online AI rewrite."
        )
        if question and question.strip():
            lines.append(f"_Your question:_ {question.strip()}")
        lines.append("")
    else:
        lines.append(
            "นี่คือข้อความใกล้เคียงที่สุดจากคลังของคุณ เป็นคำตอบแบบอ้างอิงข้อความ ไม่ใช่การเขียนใหม่ด้วย AI ออนไลน์"
        )
        if question and question.strip():
            lines.append(f"_คำถามของคุณ:_ {question.strip()}")
        lines.append("")

    for index, chunk in enumerate(chunks, start=1):
        source = str(chunk.get("source") or "").strip() or ("notes" if locale == "en" else "โน้ต")
        score = chunk.get("score")
        score_bit = f" · {float(score):.2f}" if score is not None else ""
        excerpt = _trim_excerpt(str(chunk.get("text") or ""))
        lines.append(f"**[{index}]** `{source}`{score_bit}")
        lines.append(excerpt)
        lines.append("")

    if locale == "en":
        lines.append("_Tip: Add a Groq key (with quota) for generative answers when online._")
    else:
        lines.append("_เคล็ดลับ: ใส่คีย์ Groq (และมีโควตา) เพื่อได้คำตอบแบบสร้างใหม่เมื่อออนไลน์_")
    return "\n".join(lines).rstrip() + "\n"


def resolve_knowledge_only_reply(
    chunks: list[dict[str, Any]],
    *,
    min_score: float,
    locale: str = "th",
    question: str | None = None,
) -> tuple[str, list[dict[str, Any]], bool]:
    """Filter chunks and return ``(reply, kept, has_hits)``."""
    kept = filter_passing_chunks(chunks, min_score=min_score)
    if not kept:
        return knowledge_only_empty_reply(locale=locale), [], False
    return (
        format_knowledge_only_answer(kept, locale=locale, question=question),
        kept,
        True,
    )
