# Phase 4 report — persona-bot (eval + pack I/O + bilingual)

Date: 2026-11-18 (Asia/Bangkok)  
Branch: `cursor/phase4-eval-c230`  
Repo: https://github.com/Disorn1998/PERSONAL-BOT  
Base: latest `main` (after Phase 3 PR #5)

## 1. Files created/changed

### Eval (DoD 7)
- `app/eval_harness.py` — offline/live suite runner + rates
- `tests/eval/baseline.json` — **provisional** thresholds + cases (`provisional: true`)
- `tests/eval/fixtures/eval-alpha|eval-strict/` — controlled FakeEmbedder score-gate packs
- `tests/eval/test_eval_offline.py` — CI-safe FakeEmbedder suite
- `tests/eval/test_eval_slow.py` — `@pytest.mark.slow` + `PERSONA_BOT_EVAL_LIVE=1` (manual)

### Persona pack I/O + data tools
- `app/persona_pack_io.py` — zip export/import with bomb/symlink/whitelist/duplicate/preview
- `app/backup.py` — backup / restore / delete-all (never packs `.env` / key-looking paths)
- `app/services.py` — `is_user_persona`, `persona_dir_for`
- `persona_bot/main.py` — sidebar language + Data & backup tools (no regenerate — §19 deferred)
- `tests/test_persona_pack_io.py`, `tests/test_backup.py`

### Bilingual + a11y docs
- `persona_bot/ui/strings.py` — complete `th` + `en`
- `app/i18n.py` — locale get/set + EN→TH fallback
- `docs/DESIGN.md` — accessibility checklist A1–A12
- `scripts/smoke_test.py` — expanded owner checklist
- `docs/ASSUMPTIONS.md`, `docs/DECISIONS.md`, `CHANGELOG.md`

## 2. Run/test commands

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
# Owner-only live embedder eval (not CI):
PERSONA_BOT_EVAL_LIVE=1 uv run pytest -m slow tests/eval/test_eval_slow.py
```

## 3. ruff / pytest results

| Check | Result |
|---|---|
| ruff | ✅ |
| mypy | ✅ |
| pytest | ✅ **58 passed, 1 skipped** (slow live eval skipped without env) |

## 4. Pass criteria

| Criterion | Status |
|---|---|
| Offline eval harness + committed baseline JSON | ✅ |
| Provisional hit@top_k ≥ 0.70 / OOS not-found ≥ 0.80 recorded | ✅ (ASSUMPTIONS + baseline) |
| FakeEmbedder offline suite + fixture expectations | ✅ |
| `@pytest.mark.slow` real-model path (manual) | ✅ |
| Safe zip import/export (bomb/symlink/whitelist/dup/preview) | ✅ |
| Delete user persona / delete-all / backup-restore | ✅ |
| Bilingual TH/EN via strings.py (`en` filled) | ✅ |
| `docs/DESIGN.md` a11y checklist | ✅ |
| No regenerate button (§19 deferred) | ✅ |
| DoD 7 advanced (thresholds provisional until owner lock) | ✅ advanced |
| Phase 5 not started | ✅ |

## 5. Unsure / TODO(verify)

- Real FastEmbedder hit rates on example personas (owner: `PERSONA_BOT_EVAL_LIVE=1`).
- Streamlit confirm UX for destructive actions (two-click; owner eye-check).
- Zip bomb ratio default (100:1) may be tight for already-compressed PDFs — widen if owner hits false rejects.

## 6. **ASK — lock or revise provisional eval numbers**

Owner has **not** locked DoD 7 numerics. Current provisional values in
`tests/eval/baseline.json` / `docs/ASSUMPTIONS.md`:

| Metric | Provisional |
|---|---|
| In-scope retrieval hit@top_k | **≥ 0.70** |
| Out-of-scope / not-found (strict) | **≥ 0.80** |

Please **lock or revise** these before treating DoD 7 as final.

## 7. Next phase proposal — **Phase 5**

- CI matrix expansion (3 OS) + canary (`GET /models` only) — DoD 6
- Security scanners (gitleaks / pip-audit / CodeQL) as specified
- Coverage floor decision still open (60% / 80% proposal)

**STOP.** Await owner 「ไปต่อ」 before Phase 5.
