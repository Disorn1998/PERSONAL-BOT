"""Persona schema + prompt builder / answer_mode short-circuit."""

from __future__ import annotations

from pathlib import Path

import pytest
from persona_bot.errors import KnowledgeNotFoundError
from persona_bot.persona import PersonaPack, list_example_persona_dirs, load_persona_yaml
from persona_bot.prompt import (
    build_messages,
    fixed_rules_block,
    not_found_reply_th,
    stable_system_message,
    strip_context_from_content,
)
from pydantic import ValidationError


def test_load_example_personas() -> None:
    examples = Path("personas/examples")
    dirs = list_example_persona_dirs(examples)
    ids = {p.name for p in dirs}
    assert ids == {
        "study-buddy",
        "tech-explainer",
        "writing-coach",
        "thai-tax-advisor",
        "company-faq-bot",
        "meeting-notes",
        "pdf-handbook-demo",
        "en-study-coach",
    }
    packs = [load_persona_yaml(p / "persona.yaml") for p in dirs]
    by_id = {p.id: p for p in packs}
    assert by_id["tech-explainer"].config.answer_mode == "strict"
    assert by_id["study-buddy"].config.answer_mode == "balanced"
    assert by_id["writing-coach"].config.answer_mode == "open"
    assert by_id["thai-tax-advisor"].config.answer_mode == "strict"
    assert by_id["company-faq-bot"].config.answer_mode == "strict"
    assert by_id["meeting-notes"].config.answer_mode == "balanced"
    assert by_id["pdf-handbook-demo"].config.answer_mode == "strict"
    assert by_id["en-study-coach"].config.answer_mode == "balanced"
    assert by_id["meeting-notes"].greeting
    assert by_id["thai-tax-advisor"].greeting
    assert by_id["thai-tax-advisor"].starter_questions
    assert by_id["thai-tax-advisor"].metadata.get("disclaimer_required") is True
    assert "min_score_note" in by_id["thai-tax-advisor"].metadata
    assert by_id["company-faq-bot"].icon
    assert by_id["pdf-handbook-demo"].metadata.get("disclaimer_required") is True
    assert by_id["pdf-handbook-demo"].greeting
    assert by_id["en-study-coach"].greeting
    assert by_id["en-study-coach"].metadata.get("language") == "en"
    assert any(str(p).endswith(".pdf") for p in by_id["pdf-handbook-demo"].knowledge_files)
    assert len({p.id for p in packs}) == len(packs)


def test_stable_system_includes_rules() -> None:
    pack = load_persona_yaml(Path("personas/examples/study-buddy/persona.yaml"))
    msg = stable_system_message(pack)
    assert msg["role"] == "system"
    assert pack.system_prompt.strip() in msg["content"]
    assert fixed_rules_block("balanced") in msg["content"]
    # Stability: identical across calls
    assert stable_system_message(pack) == msg


def test_strict_short_circuit_raises() -> None:
    pack = load_persona_yaml(Path("personas/examples/tech-explainer/persona.yaml"))
    with pytest.raises(KnowledgeNotFoundError):
        build_messages(
            pack,
            history=[],
            user_text="มีอะไรบ้าง?",
            context_chunks=[{"text": "irrelevant", "score": 0.01}],
        )


def test_balanced_includes_context_and_strips_history() -> None:
    pack = load_persona_yaml(Path("personas/examples/study-buddy/persona.yaml"))
    history = [
        {
            "role": "user",
            "content": "<context>\n[1]\nold\n</context>\n\nคำถามเก่า",
        },
        {"role": "assistant", "content": "คำตอบเก่า"},
    ]
    messages = build_messages(
        pack,
        history=history,
        user_text="คำถามใหม่",
        context_chunks=[{"text": "เนื้อหา", "score": 0.9, "source": "notes.md"}],
    )
    assert messages[0]["role"] == "system"
    assert messages[1]["content"] == "คำถามเก่า"
    assert "<context>" not in messages[1]["content"]
    assert messages[-1]["role"] == "user"
    assert "<context>" in messages[-1]["content"]
    assert "[1]" in messages[-1]["content"]
    assert messages[-1]["content"].endswith("คำถามใหม่")


def test_strip_context_and_not_found_copy() -> None:
    raw = "<context>\n[1]\nx\n</context>\n\nhello"
    assert strip_context_from_content(raw) == "hello"
    assert not_found_reply_th() == "ไม่พบข้อมูลที่เกี่ยวข้องในคลังความรู้"


def test_persona_validation_rejects_bad_id() -> None:
    with pytest.raises(ValidationError):
        PersonaPack(
            id="BAD ID",
            name="x",
            system_prompt="y",
        )
