"""Manual / slow eval against a real embedder (never CI).

Enable with::

    PERSONA_BOT_EVAL_LIVE=1 uv run pytest -m slow tests/eval/test_eval_slow.py
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from persona_bot.eval_harness import assert_thresholds, load_baseline, run_suite
from persona_bot.rag.embeddings import FastEmbedder

ROOT = Path(__file__).resolve().parents[2]
BASELINE = Path(__file__).resolve().parent / "baseline.json"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.mark.slow
def test_live_embedder_eval_thresholds(tmp_path: Path) -> None:
    if os.environ.get("PERSONA_BOT_EVAL_LIVE", "").strip() != "1":
        pytest.skip("set PERSONA_BOT_EVAL_LIVE=1 to run real-model eval")
    baseline = load_baseline(BASELINE)
    # Live path focuses on example personas (real multilingual embeddings).
    report = run_suite(
        baseline,
        data_dir=tmp_path / "data",
        examples_dir=ROOT / "personas" / "examples",
        personas_dir=FIXTURES,
        embedder=FastEmbedder(preset="lite"),
        suite_name="live-fastembed",
        persona_filter={"study-buddy", "tech-explainer"},
    )
    assert report.results
    assert_thresholds(report)
