"""Knowledge-only extractive answers — no Groq / no network."""

from __future__ import annotations

from persona_bot.errors import (
    LlmTransportError,
    MissingApiKeyError,
    MissingModelConfigError,
    RateLimitDayError,
    RateLimitMinuteError,
)
from persona_bot.knowledge_answer import (
    KNOWLEDGE_ONLY_BADGE_EN,
    KNOWLEDGE_ONLY_BADGE_TH,
    filter_passing_chunks,
    format_knowledge_only_answer,
    knowledge_only_badge,
    knowledge_only_empty_reply,
    resolve_knowledge_only_reply,
    should_fallback_to_knowledge_only,
)


def test_filter_passing_chunks() -> None:
    chunks = [
        {"text": "a", "score": 0.9, "source": "a.md"},
        {"text": "b", "score": 0.1, "source": "b.md"},
    ]
    kept = filter_passing_chunks(chunks, min_score=0.35)
    assert len(kept) == 1
    assert kept[0]["source"] == "a.md"


def test_should_fallback_covers_key_quota_network() -> None:
    assert should_fallback_to_knowledge_only(MissingApiKeyError())
    assert should_fallback_to_knowledge_only(MissingModelConfigError())
    assert should_fallback_to_knowledge_only(RateLimitDayError())
    assert should_fallback_to_knowledge_only(RateLimitMinuteError())
    assert should_fallback_to_knowledge_only(LlmTransportError("offline"))
    assert not should_fallback_to_knowledge_only(RuntimeError("other"))


def test_format_thai_includes_badge_and_citations() -> None:
    text = format_knowledge_only_answer(
        [{"text": "รหัส Wi-Fi คือ demo-pass-only-2026", "score": 0.82, "source": "sample-notes.md"}],
        locale="th",
        question="รหัส Wi-Fi คืออะไร?",
    )
    assert KNOWLEDGE_ONLY_BADGE_TH in text
    assert "ไม่ใช้ AI ออนไลน์" in text
    assert "[1]" in text
    assert "sample-notes.md" in text
    assert "demo-pass-only-2026" in text
    assert "ChatGPT" not in text


def test_format_english_and_empty() -> None:
    text = format_knowledge_only_answer(
        [{"text": "Meeting Friday 10:00", "score": 0.7, "source": "notes.md"}],
        locale="en",
        question="When is the meeting?",
    )
    assert KNOWLEDGE_ONLY_BADGE_EN in text
    assert "no online AI" in text.lower() or "No online AI" in text or "online AI" in text
    assert "notes.md" in text

    empty = knowledge_only_empty_reply(locale="en")
    assert "No matching" in empty
    assert knowledge_only_badge(locale="en") == KNOWLEDGE_ONLY_BADGE_EN
    assert knowledge_only_badge(locale="th") == KNOWLEDGE_ONLY_BADGE_TH


def test_resolve_knowledge_only_reply_hit_and_miss() -> None:
    chunks = [
        {"text": "pass", "score": 0.5, "source": "ok.md"},
        {"text": "fail", "score": 0.05, "source": "no.md"},
    ]
    reply, kept, has_hits = resolve_knowledge_only_reply(
        chunks, min_score=0.3, locale="th", question="?"
    )
    assert has_hits is True
    assert len(kept) == 1
    assert "ok.md" in reply

    reply2, kept2, has_hits2 = resolve_knowledge_only_reply(
        [{"text": "x", "score": 0.01}],
        min_score=0.4,
        locale="en",
    )
    assert has_hits2 is False
    assert kept2 == []
    assert "No matching" in reply2


def test_format_empty_chunks_and_long_excerpt() -> None:
    empty_th = format_knowledge_only_answer([], locale="th")
    assert "ไม่พบ" in empty_th
    long = "คำ" * 400
    text = format_knowledge_only_answer(
        [{"text": long, "score": 0.6, "source": ""}],
        locale="th",
    )
    assert "…" in text
    assert "[1]" in text
    assert knowledge_only_empty_reply(locale="th").startswith("ไม่พบ")
