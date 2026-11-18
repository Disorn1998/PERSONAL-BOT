# Changelog

All notable changes are documented here. This project follows
[Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

## [0.1.0] — 2026-11-18

First tagged release. Owner locked DoD 7 eval thresholds and overall coverage CI.

### Added

- Phase 0: repo scaffold, tooling, tokens, MIT licence
- Phase 1a/1b: config/llm/persona/prompt + Streamlit chat shell
- Phase 2: local RAG (Chroma + fastembed)
- Phase 3: start scripts, Docker, versioning, health, optional keyring
- Phase 4: offline eval harness (DoD 7 thresholds 0.70 / 0.80),
  safe persona zip I/O, backup/restore/delete-all, bilingual TH/EN, DESIGN a11y
- Phase 5: CI OS×Python matrix, pytest+cov (hard ≥60%), AppTest + contrast smokes,
  gitleaks / pip-audit / CodeQL, Docker e2e with fake Groq, weekly models canary
  (`GET /models` only), GHCR release on `v*` tags, FAQ/GALLERY/CoC/CODEOWNERS/
  issue+PR templates, expanded THIRD_PARTY_NOTICES model licence table

### Locked (2026-11-18)

- Eval DoD 7: in-scope hit@top_k **≥ 0.70**; strict OOS / not-found **≥ 0.80**
  (`tests/eval/baseline.json` `provisional: false`)
- Coverage CI: overall **≥ 60%** hard fail (`--cov-fail-under=60` /
  `fail_under = 60`); core **≥ 80%** documented as target until split coverage exists

### Notes

- Tag `v0.1.0` triggers the GHCR release workflow.

## [Unreleased]

### Added

- In-app persona create/edit (user packs under `data/personas/`) with Thai labels.
- Knowledge upload (`.txt/.md/.pdf/.docx`) + paste text; one-click index rebuild with
  plain Thai status (`พร้อมแล้ว` / `ต้องสร้างดัชนีใหม่`).
- **ทำสำเนา** duplicates an example into an editable user pack.
- README “Customize knowledge” bridge (Thai+EN).
- P1 polish: remember-key env **or** checkbox (save+load) with status text; `MAX_KNOWLEDGE_MB`
  enforcement + used/limit in Knowledge panel; 429 retry-after / reset hints on error cards;
  clear-chat confirm; localhost bind; Streamlit email skip; README/GALLERY screenshots;
  CONTRIBUTING example-persona checklist; FAQ data/PDF/strict entries; verified embedding
  licences in `THIRD_PARTY_NOTICES.md`.

### Changed

- Renamed importable package `app` → `persona_bot` (Docker `WORKDIR` still `/app`).
- Restored §9 example personas `thai-tax-advisor` + `company-faq-bot` (fictional knowledge).
- Persona schema: optional `icon`, `greeting`, `starter_questions`, `metadata`.
- CI: LF via `.gitattributes`, gitleaks test-fixture allowlist, pip-audit chromadb waives.
- CLI forces `--server.address=127.0.0.1`; `.streamlit/config.toml` matches.
