# Contributing

1. Use Python **3.11–3.13** and [uv](https://docs.astral.sh/uv/).
2. `uv sync --extra dev` then optional `uv run pre-commit install`.
3. Before a PR run:

   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy
   uv run pytest -m "not slow" --cov=app --cov-fail-under=60
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

Coverage: overall **≥ 60%** hard-fail; core **≥ 80%** target when split coverage exists.
