"""Offline / slow evaluation helpers for retrieval thresholds (DoD 7)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from persona_bot.persona import PersonaPack, load_persona_yaml
from persona_bot.prompt import should_short_circuit_strict
from persona_bot.rag.embeddings import Embedder, FakeEmbedder
from persona_bot.rag.ingest import ensure_index, knowledge_dir_for_persona
from persona_bot.rag.retrieve import retrieve
from persona_bot.rag.store import VectorStore

CaseKind = Literal["in_scope", "out_of_scope"]


@dataclass(slots=True)
class EvalThresholds:
    in_scope_hit_at_top_k: float = 0.70
    out_of_scope_not_found_rate: float = 0.80


@dataclass(slots=True)
class EvalCase:
    id: str
    persona_id: str
    kind: CaseKind
    query: str
    previous_user: str | None = None
    expect_source_contains: str | None = None
    expect_text_contains: list[str] = field(default_factory=list)
    offline_mode: Literal["score_gate", "fixture_expectation"] = "fixture_expectation"
    min_score_override: float | None = None


@dataclass(slots=True)
class CaseResult:
    case_id: str
    persona_id: str
    kind: CaseKind
    passed: bool
    top_score: float | None
    top_source: str | None
    detail: str
    hit: bool = False
    treated_as_not_found: bool = False


@dataclass(slots=True)
class EvalReport:
    suite: str
    thresholds: EvalThresholds
    results: list[CaseResult]
    provisional: bool = False

    @property
    def in_scope_hit_rate(self) -> float:
        cases = [r for r in self.results if r.kind == "in_scope"]
        if not cases:
            return 1.0
        return sum(1 for r in cases if r.hit) / len(cases)

    @property
    def out_of_scope_not_found_rate(self) -> float:
        cases = [r for r in self.results if r.kind == "out_of_scope"]
        if not cases:
            return 1.0
        return sum(1 for r in cases if r.treated_as_not_found) / len(cases)

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite": self.suite,
            "provisional": self.provisional,
            "thresholds": asdict(self.thresholds),
            "in_scope_hit_rate": self.in_scope_hit_rate,
            "out_of_scope_not_found_rate": self.out_of_scope_not_found_rate,
            "results": [asdict(r) for r in self.results],
        }


def load_baseline(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        msg = "baseline.json must be an object"
        raise ValueError(msg)
    return data


def parse_thresholds(raw: dict[str, Any]) -> EvalThresholds:
    t = raw.get("thresholds") or {}
    return EvalThresholds(
        in_scope_hit_at_top_k=float(t.get("in_scope_hit_at_top_k", 0.70)),
        out_of_scope_not_found_rate=float(t.get("out_of_scope_not_found_rate", 0.80)),
    )


def parse_cases(raw: dict[str, Any]) -> list[EvalCase]:
    cases: list[EvalCase] = []
    for item in raw.get("cases") or []:
        cases.append(
            EvalCase(
                id=str(item["id"]),
                persona_id=str(item["persona_id"]),
                kind=item["kind"],
                query=str(item["query"]),
                previous_user=item.get("previous_user"),
                expect_source_contains=item.get("expect_source_contains"),
                expect_text_contains=list(item.get("expect_text_contains") or []),
                offline_mode=item.get("offline_mode") or "fixture_expectation",
                min_score_override=(
                    float(item["min_score_override"])
                    if item.get("min_score_override") is not None
                    else None
                ),
            )
        )
    return cases


def _history_for(case: EvalCase) -> list[dict[str, str]]:
    if not case.previous_user:
        return []
    return [{"role": "user", "content": case.previous_user}]


def run_case(
    case: EvalCase,
    *,
    persona: PersonaPack,
    store: VectorStore,
    thresholds: EvalThresholds,
) -> CaseResult:
    min_score = (
        case.min_score_override
        if case.min_score_override is not None
        else persona.config.resolved_min_score()
    )
    top_k = persona.config.resolved_top_k()
    hits = retrieve(
        store,
        persona_id=persona.id,
        latest=case.query,
        history=_history_for(case),
        top_k=top_k,
        min_score=0.0,
    )
    top = hits[0] if hits else None
    top_score = float(top["score"]) if top else None
    top_source = str(top.get("source") or "") if top else None

    if case.kind == "in_scope":
        hit = False
        detail = "miss"
        if case.offline_mode == "score_gate":
            hit = top_score is not None and top_score >= thresholds.in_scope_hit_at_top_k
            if case.expect_source_contains and top_source:
                hit = hit and case.expect_source_contains in top_source
            detail = f"top_score={top_score} gate={thresholds.in_scope_hit_at_top_k}"
        else:
            # Fixture expectation: expected tokens / source appear in top_k hits.
            pool = hits[:top_k]
            blob = " ".join(f"{h.get('source', '')} {h.get('text', '')}" for h in pool)
            ok_source = True
            if case.expect_source_contains:
                ok_source = any(
                    case.expect_source_contains in str(h.get("source") or "") for h in pool
                )
            ok_text = True
            if case.expect_text_contains:
                ok_text = all(tok in blob for tok in case.expect_text_contains)
            hit = bool(pool) and ok_source and ok_text
            detail = f"fixture_expectation source_ok={ok_source} text_ok={ok_text}"
        return CaseResult(
            case_id=case.id,
            persona_id=case.persona_id,
            kind=case.kind,
            passed=hit,
            top_score=top_score,
            top_source=top_source,
            detail=detail,
            hit=hit,
        )

    # out_of_scope — strict personas must treat as not-found / below min_score
    passing = [h for h in hits if float(h.get("score", 0.0)) >= min_score]
    treated = should_short_circuit_strict(
        answer_mode=persona.config.answer_mode,
        scored_chunks=passing if passing else hits,
        min_score=min_score,
    )
    # Also accept: zero hits, or all scores below min_score.
    no_pass = not passing
    treated = no_pass if persona.config.answer_mode != "strict" else no_pass or treated
    detail = f"passing={len(passing)} min_score={min_score} top={top_score}"
    return CaseResult(
        case_id=case.id,
        persona_id=case.persona_id,
        kind=case.kind,
        passed=treated,
        top_score=top_score,
        top_source=top_source,
        detail=detail,
        treated_as_not_found=treated,
    )


def index_persona(
    *,
    persona: PersonaPack,
    data_dir: Path,
    examples_dir: Path,
    personas_dir: Path,
    embedder: Embedder,
) -> VectorStore:
    store = VectorStore(data_dir=data_dir, embedder=embedder)
    kdir = knowledge_dir_for_persona(
        examples_dir=examples_dir,
        personas_dir=personas_dir,
        persona_id=persona.id,
    )
    ensure_index(store, persona=persona, knowledge_dir=kdir, force=True)
    return store


def run_suite(
    baseline: dict[str, Any],
    *,
    data_dir: Path,
    examples_dir: Path,
    personas_dir: Path,
    embedder: Embedder | None = None,
    suite_name: str = "offline",
    persona_filter: set[str] | None = None,
) -> EvalReport:
    thresholds = parse_thresholds(baseline)
    cases = parse_cases(baseline)
    emb = embedder or FakeEmbedder(dim=32, model_name="fake:eval")
    cache: dict[str, tuple[PersonaPack, VectorStore]] = {}
    results: list[CaseResult] = []

    for case in cases:
        if persona_filter and case.persona_id not in persona_filter:
            continue
        if case.persona_id not in cache:
            # Prefer user personas_dir, else examples.
            user_yaml = personas_dir / case.persona_id / "persona.yaml"
            example_yaml = examples_dir / case.persona_id / "persona.yaml"
            yaml_path = user_yaml if user_yaml.exists() else example_yaml
            persona = load_persona_yaml(yaml_path)
            store = index_persona(
                persona=persona,
                data_dir=data_dir,
                examples_dir=examples_dir,
                personas_dir=personas_dir,
                embedder=emb,
            )
            cache[case.persona_id] = (persona, store)
        persona, store = cache[case.persona_id]
        results.append(run_case(case, persona=persona, store=store, thresholds=thresholds))

    return EvalReport(
        suite=suite_name,
        thresholds=thresholds,
        results=results,
        provisional=bool(baseline.get("provisional", False)),
    )


def assert_thresholds(report: EvalReport, *, apply_score_gate_only: bool = False) -> None:
    """Raise AssertionError when suite rates miss locked DoD 7 thresholds."""
    in_scope = [r for r in report.results if r.kind == "in_scope"]
    oos = [r for r in report.results if r.kind == "out_of_scope"]
    if apply_score_gate_only:
        in_scope = [r for r in in_scope if "gate=" in r.detail]
    if in_scope:
        rate = sum(1 for r in in_scope if r.hit) / len(in_scope)
        if rate + 1e-9 < report.thresholds.in_scope_hit_at_top_k:
            msg = f"in_scope hit rate {rate:.3f} < {report.thresholds.in_scope_hit_at_top_k:.3f}"
            raise AssertionError(msg)
    if oos:
        rate = sum(1 for r in oos if r.treated_as_not_found) / len(oos)
        if rate + 1e-9 < report.thresholds.out_of_scope_not_found_rate:
            msg = (
                f"out_of_scope not-found rate {rate:.3f} < "
                f"{report.thresholds.out_of_scope_not_found_rate:.3f}"
            )
            raise AssertionError(msg)
