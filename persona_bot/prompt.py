"""Prompt builder — stable system prefix (cache-friendly) + answer_mode rules."""

from __future__ import annotations

from typing import Any, Literal

from persona_bot.errors import KnowledgeNotFoundError
from persona_bot.persona import AnswerMode, PersonaPack

Role = Literal["system", "user", "assistant"]

# Built-in rules blocks — byte-stable defaults (prompt-caching friendly).
# User packs may override per mode via ``config.answer_rules``.
DEFAULT_ANSWER_RULES: dict[AnswerMode, str] = {
    "strict": (
        "### Fixed rules (strict)\n"
        "- Answer ONLY using the numbered <context> snippets when present.\n"
        "- If context is missing or insufficient, reply with the exact Thai phrase "
        "「ไม่พบข้อมูลที่เกี่ยวข้องในคลังความรู้」 and nothing else.\n"
        "- Do not invent facts. Cite sources as [n] matching context numbers.\n"
        "- Keep the persona voice from the system prompt.\n"
    ),
    "balanced": (
        "### Fixed rules (balanced)\n"
        "- Prefer the numbered <context> snippets; cite as [n] when used.\n"
        "- If context is weak, say so briefly in Thai, then give a careful best-effort "
        "answer in the persona voice without fabricating citations.\n"
        "- Stay helpful and concise.\n"
    ),
    "open": (
        "### Fixed rules (open)\n"
        "- Use <context> when helpful; citations [n] are optional but must be valid.\n"
        "- You may use general knowledge consistent with the persona.\n"
        "- Stay helpful and concise.\n"
    ),
}

# Back-compat alias used by older tests / imports.
_RULES = DEFAULT_ANSWER_RULES


def default_rules_block(answer_mode: AnswerMode) -> str:
    """Built-in rules text for ``answer_mode`` (always available)."""
    return DEFAULT_ANSWER_RULES[answer_mode]


def fixed_rules_block(
    answer_mode: AnswerMode,
    *,
    custom_rules: str | None = None,
) -> str:
    """Rules block for a mode — custom override when non-empty, else built-in."""
    text = (custom_rules or "").strip()
    if text:
        return text if text.endswith("\n") else f"{text}\n"
    return default_rules_block(answer_mode)


def resolve_answer_rules(
    persona: PersonaPack,
    *,
    answer_mode: AnswerMode | None = None,
) -> str:
    """Effective rules for a persona (override from ``config.answer_rules`` or default)."""
    mode: AnswerMode = answer_mode or persona.config.answer_mode
    custom = persona.config.answer_rules.get(mode)
    return fixed_rules_block(mode, custom_rules=custom)


def stable_system_message(persona: PersonaPack) -> dict[str, str]:
    """System message that must stay byte-identical every turn for a persona."""
    body = persona.system_prompt.rstrip() + "\n\n" + resolve_answer_rules(persona)
    return {"role": "system", "content": body}


def format_context_block(chunks: list[dict[str, Any]]) -> str:
    """Render numbered context. Each chunk: ``{text, source?}``."""
    lines: list[str] = ["<context>"]
    for index, chunk in enumerate(chunks, start=1):
        source = chunk.get("source") or ""
        header = f"[{index}]" + (f" ({source})" if source else "")
        text = str(chunk.get("text", "")).strip()
        lines.append(f"{header}\n{text}")
    lines.append("</context>")
    return "\n".join(lines)


def strip_context_from_content(content: str) -> str:
    """Remove a prior turn's <context>…</context> block from history messages."""
    start = content.find("<context>")
    end = content.find("</context>")
    if start == -1 or end == -1 or end < start:
        return content
    end += len("</context>")
    cleaned = (content[:start] + content[end:]).strip()
    return cleaned


def should_short_circuit_strict(
    *,
    answer_mode: AnswerMode,
    scored_chunks: list[dict[str, Any]],
    min_score: float,
) -> bool:
    """True when strict mode has no knowledge passing ``min_score``."""
    if answer_mode != "strict":
        return False
    if not scored_chunks:
        return True
    return all(float(c.get("score", 0.0)) < min_score for c in scored_chunks)


def build_messages(
    persona: PersonaPack,
    *,
    history: list[dict[str, str]],
    user_text: str,
    context_chunks: list[dict[str, Any]] | None = None,
    min_score: float | None = None,
) -> list[dict[str, str]]:
    """Assemble chat messages for the LLM.

    History entries must be ``{role, content}``. Old user turns are stored
    **without** their ``<context>`` blocks (caller may pass raw; we strip).
    """
    threshold = min_score if min_score is not None else persona.config.resolved_min_score()
    chunks = list(context_chunks or [])
    if should_short_circuit_strict(
        answer_mode=persona.config.answer_mode,
        scored_chunks=chunks,
        min_score=threshold,
    ):
        raise KnowledgeNotFoundError(details={"min_score": threshold})

    messages: list[dict[str, str]] = [stable_system_message(persona)]
    for turn in history:
        role = turn.get("role", "")
        content = turn.get("content", "")
        if role not in {"user", "assistant"}:
            continue
        if role == "user":
            content = strip_context_from_content(content)
        messages.append({"role": role, "content": content})

    user_payload = user_text.strip()
    if chunks:
        # Keep only chunks that pass min_score for the prompt body.
        kept = [c for c in chunks if float(c.get("score", 1.0)) >= threshold]
        if kept:
            user_payload = format_context_block(kept) + "\n\n" + user_payload
    messages.append({"role": "user", "content": user_payload})
    return messages


def not_found_reply_th() -> str:
    return "ไม่พบข้อมูลที่เกี่ยวข้องในคลังความรู้"
