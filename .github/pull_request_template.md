## Summary

<!-- What changed and why -->

## Phase / DoD

- [ ] Matches current phase scope only (no drive-by Phase N+1)
- [ ] Docs/ASSUMPTIONS or DECISIONS updated if assumptions changed

## Test plan

- [ ] `uv run ruff check .`
- [ ] `uv run ruff format --check .`
- [ ] `uv run mypy`
- [ ] `uv run pytest -m "not slow"`
- [ ] No real Groq `chat/completions` in CI/tests
- [ ] No secrets / `.env` / `data/` committed
