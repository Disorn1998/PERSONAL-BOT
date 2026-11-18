# Contributing

1. Use Python 3.11–3.13 and [uv](https://docs.astral.sh/uv/).
2. `uv sync --extra dev` then `uv run pre-commit install` (optional).
3. Run `uv run ruff check .`, `uv run mypy`, `uv run pytest` before opening a PR.
4. Never commit `.env`, `data/`, or API keys.
5. Do not call real Groq from unit tests / CI — use mocks + `FakeEmbedder`.
6. Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
7. One phase at a time per the master prompt; stop for owner 「ไปต่อ」.
