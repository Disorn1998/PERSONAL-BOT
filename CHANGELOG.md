# Changelog

All notable changes are documented here. This project follows
[Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

## [0.1.0] — 2026-11-18

### Added

- Phase 0: repo scaffold, tooling, tokens, MIT licence
- Phase 1a/1b: config/llm/persona/prompt + Streamlit chat shell
- Phase 2: local RAG (Chroma + fastembed)
- Phase 3: start scripts, Docker, versioning, health, optional keyring
- Phase 4: offline eval harness (provisional DoD 7 thresholds 0.70 / 0.80),
  safe persona zip I/O, backup/restore/delete-all, bilingual TH/EN, DESIGN a11y
- Phase 5: CI OS×Python matrix, pytest+cov (soft), AppTest + contrast smokes,
  gitleaks / pip-audit / CodeQL, Docker e2e with fake Groq, weekly models canary
  (`GET /models` only), GHCR release on `v*` tags, FAQ/GALLERY/CoC/CODEOWNERS/
  issue+PR templates, expanded THIRD_PARTY_NOTICES model licence table

### Notes

- Eval thresholds remain **provisional** until the owner locks them.
- Coverage floors (~60% / ~80%) remain **unlocked** (`fail_under=0`).
