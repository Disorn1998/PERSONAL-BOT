# Phase 2 report — persona-bot (RAG)

Date: 2026-11-18 (Asia/Bangkok)  
Branch: `cursor/phase2-rag-c230` (based on **main after PR #3 / Phase 1b merge**)  
Repo: https://github.com/Disorn1998/PERSONAL-BOT

## Note on Phase 1b

PR [#3](https://github.com/Disorn1998/PERSONAL-BOT/pull/3) was still open when Phase 2 started; work briefly stacked on `cursor/phase1b-chat-shell-c230`, then **rebased onto latest main** after #3 merged. No duplicate 1b work.

## 1. Files created/changed

### RAG package
- `app/rag/loaders.py` — txt/md/pdf/docx
- `app/rag/chunking.py` — char chunker + overlap
- `app/rag/embeddings.py` — `FastEmbedder` + `FakeEmbedder`
- `app/rag/fingerprint.py` — index fingerprint
- `app/rag/store.py` — Chroma persistent store + atomic rebuild + manifest
- `app/rag/ingest.py` — ensure index / collect chunks
- `app/rag/retrieve.py` — query = prev user + latest; min_score filter
- `app/rag/citations.py` — `[n]` validation + sources markdown
- `app/rag/health.py` — knowledge-health summary
- `app/rag/search_lab.py` — search-lab helper
- `app/rag/prompt_inspector.py` — prompt summary
- `app/rag/runtime.py` — UI/session wiring

### UI / examples / docs
- `persona_bot/main.py` — retrieve → build_messages → budget → stream; sources + citation warn + inspector
- `persona_bot/ui/strings.py` — knowledge / search-lab / rebuild keys
- `personas/examples/study-buddy/knowledge/*`, `tech-explainer/knowledge/*`
- `docs/ASSUMPTIONS.md`, `docs/DECISIONS.md`, `docs/phase2-report.md`
- `tests/test_rag.py` — FakeEmbedder + hypothesis chunking + PDF loader smoke

## 2. Run/test commands

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

## 3. ruff / pytest results

| Check | Result |
|---|---|
| ruff | ✅ |
| mypy | ✅ |
| pytest | ✅ **39 passed** (incl. hypothesis) |

## 4. Pass criteria

| Criterion | Status |
|---|---|
| Loaders / chunker / embedder / store | ✅ |
| budget wiring (still via `fit_prompt` before LLM) | ✅ |
| knowledge UI + sources expander | ✅ |
| Thai content (md/txt) + PDF loader + hypothesis chunking | ✅ |
| index_fingerprint + atomic rebuild | ✅ |
| retrieval = latest + previous user | ✅ |
| citation check | ✅ |
| strict + min_score short-circuit (no LLM) | ✅ |
| search-lab / knowledge-health / prompt inspector | ✅ |
| chat_store extended via message meta (sources/citations) | ✅ |
| DoD 2 (in-file + strict short-circuit) | ✅ advanced |
| DoD 5 (refresh keeps history; chunk_chars rebuild) | ✅ (sqlite history; fingerprint on chunk_chars) |
| Phase 3 not started | ✅ |

## 5. Unsure / TODO(verify)

- First UI load downloads fastembed ONNX weights (network + disk).
- Thai text extraction quality from real-world PDFs with complex fonts.
- FakeEmbedder ranking ≠ production semantic quality — owner smoke_test later.
- Exact §16 wording for search-lab / inspector if originals differ.

## 6. Next phase proposal — **Phase 3**

- Windows `start.bat` / mac `start.command` / `start.sh` ≈5 min fresh start (DoD 1)
- Docker optional packaging
- Harden first-run model download UX / offline cache docs
- Optional keyring remember-key path

**STOP.** Await owner 「ไปต่อ」 before Phase 3.
