"""Token budget fitting for chat prompts (heuristic; no paid tokenizer)."""

from __future__ import annotations

from typing import Any

# Rough multilingual heuristic — Thai/English mix. TODO(verify) against tiktoken/Groq.
CHARS_PER_TOKEN = 3.0
DEFAULT_CONTEXT_WINDOW = 8192
DEFAULT_REPLY_RESERVE = 1024
DEFAULT_SYSTEM_RESERVE = 0


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, int(len(text) / CHARS_PER_TOKEN) + 1)


def message_tokens(message: dict[str, Any]) -> int:
    content = str(message.get("content", ""))
    # Small per-message overhead for role framing.
    return estimate_tokens(content) + 4


def total_tokens(messages: list[dict[str, Any]]) -> int:
    return sum(message_tokens(m) for m in messages)


def fit_prompt(
    messages: list[dict[str, Any]],
    *,
    context_window: int = DEFAULT_CONTEXT_WINDOW,
    reply_reserve: int = DEFAULT_REPLY_RESERVE,
) -> list[dict[str, Any]]:
    """Trim oldest history turns while keeping system + latest user message.

    Preserves message[0] when it is ``system``, and always keeps the final
    user message. Drops oldest user/assistant pairs from the middle first.
    """
    if not messages:
        return []
    budget = max(512, context_window - reply_reserve)
    fitted = [dict(m) for m in messages]
    if total_tokens(fitted) <= budget:
        return fitted

    system: list[dict[str, Any]] = []
    rest = fitted
    if fitted and fitted[0].get("role") == "system":
        system = [fitted[0]]
        rest = fitted[1:]

    if not rest:
        return system

    latest = rest[-1]
    middle = rest[:-1]

    while middle and total_tokens(system + middle + [latest]) > budget:
        # Drop oldest turn (prefer dropping a full user+assistant pair).
        middle.pop(0)
        if middle and middle[0].get("role") == "assistant":
            middle.pop(0)

    # If still too large, truncate the latest user content (keep a tail).
    result = system + middle + [latest]
    if total_tokens(result) > budget and latest.get("role") == "user":
        overhead = total_tokens(system + middle) + 4
        allowed_chars = max(200, int((budget - overhead) * CHARS_PER_TOKEN))
        content = str(latest.get("content", ""))
        if len(content) > allowed_chars:
            latest = {
                **latest,
                "content": "…\n" + content[-allowed_chars:],
            }
            result = system + middle + [latest]
    return result
