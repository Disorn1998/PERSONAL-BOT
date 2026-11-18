"""Prompt inspector — summarize assembled messages for debugging (Phase 2)."""

from __future__ import annotations

from typing import Any

from app.budget import estimate_tokens, total_tokens


def inspect_messages(messages: list[dict[str, Any]]) -> dict[str, Any]:
    roles = [str(m.get("role")) for m in messages]
    system = next((m for m in messages if m.get("role") == "system"), None)
    latest = messages[-1] if messages else None
    has_context = False
    if latest and isinstance(latest.get("content"), str):
        has_context = "<context>" in latest["content"]
    return {
        "message_count": len(messages),
        "roles": roles,
        "approx_tokens": total_tokens(messages),
        "system_chars": len(str(system.get("content", ""))) if system else 0,
        "system_tokens_approx": estimate_tokens(str(system.get("content", ""))) if system else 0,
        "latest_has_context": has_context,
        "latest_role": latest.get("role") if latest else None,
    }
