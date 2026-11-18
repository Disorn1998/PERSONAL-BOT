"""Local usage tracker persisted to ``data/usage.json`` (no secrets)."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from persona_bot.llm import StreamResult, TokenUsage


@dataclass(slots=True)
class UsageSnapshot:
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cached_tokens: int = 0
    request_count: int = 0
    by_model: dict[str, int] = field(default_factory=dict)
    updated_at: float = 0.0


class UsageTracker:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> UsageSnapshot:
        if not self.path.exists():
            return UsageSnapshot()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return UsageSnapshot()
        return UsageSnapshot(
            total_prompt_tokens=int(raw.get("total_prompt_tokens", 0)),
            total_completion_tokens=int(raw.get("total_completion_tokens", 0)),
            total_tokens=int(raw.get("total_tokens", 0)),
            total_cached_tokens=int(raw.get("total_cached_tokens", 0)),
            request_count=int(raw.get("request_count", 0)),
            by_model={str(k): int(v) for k, v in dict(raw.get("by_model") or {}).items()},
            updated_at=float(raw.get("updated_at", 0.0)),
        )

    def save(self) -> None:
        self._data.updated_at = time.time()
        payload: dict[str, Any] = asdict(self._data)
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    @property
    def snapshot(self) -> UsageSnapshot:
        return self._data

    def record(self, result: StreamResult) -> None:
        usage: TokenUsage = result.usage
        self._data.total_prompt_tokens += usage.prompt_tokens
        self._data.total_completion_tokens += usage.completion_tokens
        self._data.total_tokens += usage.total_tokens
        self._data.total_cached_tokens += usage.cached_tokens
        self._data.request_count += 1
        if result.model:
            self._data.by_model[result.model] = (
                self._data.by_model.get(result.model, 0) + usage.total_tokens
            )
        self.save()


def format_token_usage(*, total_tokens: int, daily_limit: int | None) -> str:
    """Display-only token counter; ``daily_limit`` is a soft F12 hint (not enforced)."""
    if daily_limit is None or daily_limit <= 0:
        return str(total_tokens)
    return f"{total_tokens} / {daily_limit}"
