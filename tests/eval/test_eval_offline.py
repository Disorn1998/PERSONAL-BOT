"""Offline eval suite — FakeEmbedder only (CI-safe)."""

from __future__ import annotations

from pathlib import Path

from app.eval_harness import assert_thresholds, load_baseline, run_suite
from app.rag.embeddings import FakeEmbedder

ROOT = Path(__file__).resolve().parents[2]
BASELINE = Path(__file__).resolve().parent / "baseline.json"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_offline_eval_meets_locked_thresholds(tmp_path: Path) -> None:
    baseline = load_baseline(BASELINE)
    report = run_suite(
        baseline,
        data_dir=tmp_path / "data",
        examples_dir=ROOT / "personas" / "examples",
        personas_dir=FIXTURES,
        embedder=FakeEmbedder(dim=32, model_name="fake:eval"),
        suite_name="offline-fake",
    )
    assert report.results, "expected eval cases"
    # Per-case fixture expectations must pass.
    failed = [r for r in report.results if not r.passed]
    assert not failed, {r.case_id: r.detail for r in failed}
    # Score-gate subset + OOS rates vs locked DoD 7 thresholds.
    assert_thresholds(report)
    assert report.provisional is False
    assert report.in_scope_hit_rate + 1e-9 >= report.thresholds.in_scope_hit_at_top_k
    assert (
        report.out_of_scope_not_found_rate + 1e-9 >= report.thresholds.out_of_scope_not_found_rate
    )


def test_baseline_json_schema() -> None:
    baseline = load_baseline(BASELINE)
    assert baseline["schema_version"] == 1
    assert baseline["provisional"] is False
    assert baseline.get("locked_at") == "2026-11-18"
    assert "thresholds" in baseline
    assert baseline["thresholds"]["in_scope_hit_at_top_k"] == 0.70
    assert baseline["thresholds"]["out_of_scope_not_found_rate"] == 0.80
    assert any(c["persona_id"] == "eval-alpha" for c in baseline["cases"])
