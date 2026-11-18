"""Usage tracker persistence."""

from __future__ import annotations

from pathlib import Path

from persona_bot.llm import StreamResult, TokenUsage
from persona_bot.usage import UsageTracker


def test_usage_records_and_persists(tmp_path: Path) -> None:
    path = tmp_path / "usage.json"
    tracker = UsageTracker(path)
    result = StreamResult(
        model="model-a",
        usage=TokenUsage(prompt_tokens=5, completion_tokens=7, total_tokens=12, cached_tokens=2),
    )
    tracker.record(result)
    assert path.exists()
    again = UsageTracker(path)
    assert again.snapshot.total_tokens == 12
    assert again.snapshot.by_model["model-a"] == 12
    assert again.snapshot.request_count == 1
