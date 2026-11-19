# Contributing

1. Use Python **3.11–3.13** and [uv](https://docs.astral.sh/uv/).
2. `uv sync --extra dev` then optional `uv run pre-commit install`.
3. Before a PR run:

   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy
   uv run pytest -m "not slow" --cov=persona_bot --cov-fail-under=60
   uv run coverage report --rcfile=coverage.core.toml
   ```

4. Never commit `.env`, `data/`, or API keys.
5. Do not call real Groq `chat/completions` from unit tests / CI — use mocks +
   `FakeEmbedder`. The weekly canary may call **`GET /models` only**.
6. Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
7. Follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
8. Security reports: see [SECURITY.md](SECURITY.md).
9. Docs: update `docs/ASSUMPTIONS.md` / `docs/DECISIONS.md` when you assume.

## CI overview

| Workflow | Purpose |
|---|---|
| `ci.yml` | OS×Python matrix, ruff/mypy/pytest+cov, Docker e2e + fake Groq |
| `security.yml` | gitleaks, pip-audit, CodeQL (public) |
| `canary.yml` | Weekly `GET /models` vs `.env.example` |
| `release.yml` | Tag `v*` → GHCR image |

Coverage gates (both hard-fail in CI):

| Gate | Floor | How |
|---|---|---|
| Overall `persona_bot` | **≥ 60%** | `pytest --cov=persona_bot --cov-fail-under=60` |
| Core (omit Streamlit shell) | **≥ 80%** | `coverage report --rcfile=coverage.core.toml` |

Core omitlist (see `coverage.core.toml` / `docs/DECISIONS.md`): `main.py`, `ui/*`,
`eval_harness.py`, `backup.py`, `cli.py`, `versioning.py`. Do not require `main.py`
or overall ≥80% — Streamlit AppTest coverage is still thin.

## Adding an example persona

Checklist for a new pack under `personas/examples/<id>/`:

1. **Folder layout**
   ```text
   personas/examples/<id>/
     persona.yaml
     knowledge/          # optional; .txt .md .pdf .docx only
       *.md
   ```
2. **`persona.yaml` fields** (required unless noted)
   - `id` — lowercase `a-z0-9_-`, must match folder name
   - `name`, `description`, `system_prompt`
   - `config.answer_mode` — `strict` | `balanced` | `open`
   - `config.temperature`, `config.max_tokens`, `config.embedding_preset`
   - Optional: `icon`, `greeting`, `starter_questions`, `metadata`, retrieval knobs
     (`top_k`, `min_score`, `chunk_chars`)
3. **Fictional-knowledge rule**  
   Example knowledge must be **self-written demo content** (no scraped proprietary docs,
   no real personal data, no “real legal/tax advice” framing). Tax/FAQ-style packs need an
   explicit disclaimer file in `knowledge/`.
4. **Gallery row** — add the pack to the table in [`docs/GALLERY.md`](docs/GALLERY.md).
5. **Tests** — at least one offline assertion that the pack loads
   (e.g. extend `tests/test_services.py` / persona load coverage) and, for `strict` packs,
   prefer an eval fixture or RAG smoke that exercises not-found vs in-scope hits.
6. **Do not** commit API keys, `.env`, or files under `data/`.
7. Keep README/FAQ pointers accurate if the pack introduces a new user-facing workflow.
