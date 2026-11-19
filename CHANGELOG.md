# Changelog

All notable changes are documented here. This project follows
[Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

## [Unreleased]

### Changed

- Beginner sidebar: default shows language, persona, chat, knowledge, and
  「ตั้งค่า」; usage / version / persona editor / backup / health / Advanced labs
  live under collapsed「ตั้งค่าเพิ่มเติม」. Shorter TH/EN labels; version display
  prefers checkout `APP_VERSION` over a stale installed wheel.

## [0.2.2] — 2026-11-19

Patch release after `v0.2.1`: everyday offline UX (#22) + soft polish (fonts, AppTest).

### Added

- Everyday beginner UX: 「สำหรับคนทั่วไป」 docs path; simple persona editor with lab
  knobs under Advanced; plain answer-mode labels; auto-rebuild after
  upload/paste (「บันทึกความรู้ให้พร้อมใช้」); calm strict OOS; search lab / prompt
  inspector buried under Advanced.
- Knowledge-only answers when no Groq key, quota exhausted (429), or network fails:
  extractive Thai+EN replies labeled 「ตอบจากคลังความรู้ (ไม่ใช้ AI ออนไลน์)」.
- Example persona `personal-notes` /「โน้ตส่วนตัว」guided template (fictional sample).
- Bundled OFL UI fonts under `persona_bot/static/fonts/` (Inter + Noto Sans Thai
  woff2); theme injects base64 `@font-face` (no CDN). Licences in
  `THIRD_PARTY_NOTICES.md`.
- Deeper Streamlit AppTest: knowledge-only continue, clear-chat confirm, create
  persona, and paste→「บันทึกความรู้ให้พร้อมใช้」with FakeEmbedder (no Groq).

### Docs

- README / FIRST_RUN / FAQ: what this is/isn’t, zip multi-device, honest offline
  and token limits; Docker Desktop as non-dev path A.

### Notes

- Tag `v0.2.2` triggers the GHCR release workflow (`:v0.2.2` + `:latest`).

## [0.2.1] — 2026-11-19

Patch release after `v0.2.0`: core coverage gate + two example personas.

### Added

- Phased **core coverage ≥80%** CI gate (`coverage.core.toml`) omitting Streamlit
  shell (`main.py`), `ui/*`, eval harness, and backup/cli/versioning helpers;
  overall gate stays **≥60%** (PR #19).
- Example personas: `pdf-handbook-demo` (strict, tiny fictional PDFs + disclaimer)
  and `en-study-coach` (balanced, English-first study notes) (PR #20).

### Notes

- Tag `v0.2.1` triggers the GHCR release workflow (`:v0.2.1` + `:latest`).

## [0.2.0] — 2026-11-18

Minor release: in-app persona editor + public-readiness P1/P2 polish after `v0.1.1`.

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
- P2 polish: first-run wizard progress steps; advanced sidebar tools gated until API key;
  `DAILY_TOKEN_LIMIT` in usage sidebar; single-click persona zip download; overwrite-import
  confirm; Windows troubleshooting (uv PATH / SmartScreen / long paths); example
  `meeting-notes` persona.

### Changed

- CLI forces `--server.address=127.0.0.1`; `.streamlit/config.toml` matches.

### Notes

- Tag `v0.2.0` triggers the GHCR release workflow (`:v0.2.0` + `:latest`).

## [0.1.1] — 2026-11-18

Retrospective section for tag `v0.1.1` (rename + examples + CI greens).
`pyproject.toml` was not bumped at tag time; package metadata stayed `0.1.0` until `0.2.0`.

### Changed

- Renamed importable package `app` → `persona_bot` (Docker `WORKDIR` still `/app`).
- Restored §9 example personas `thai-tax-advisor` + `company-faq-bot` (fictional knowledge).
- Persona schema: optional `icon`, `greeting`, `starter_questions`, `metadata`.
- CI: LF via `.gitattributes`, gitleaks test-fixture allowlist, pip-audit chromadb waives.

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
