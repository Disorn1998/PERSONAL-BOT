# Security

## Reporting

Report vulnerabilities privately to the repository owner
([@Disorn1998](https://github.com/Disorn1998)).
Do not file public issues that include live API keys or personal chat logs.

## Practices

- Bring your own Groq key (BYOK). Keys stay in session by default.
- Optional OS keyring (`PERSONA_BOT_REMEMBER_KEY=1` **or** the UI “remember key” checkbox)
  stores the key **outside** `data/` and enables both save and load across restarts.
- Never commit `.env` or anything under `data/`.
- Logs redact API-key-like strings (`persona_bot/security.py`).
- Persona zip import rejects path traversal, symlinks, non-whitelist members, and zip bombs.
- Backups skip `.env` / api-key-looking paths; never put secrets in export zips.
- `APP_PASSWORD` is a simple local gate — **not** multi-user auth.
- CI never calls Groq `chat/completions`. Weekly canary may call `GET /models` only
  (maintainer `GROQ_API_KEY` secret; skipped on forks).

## Automated scanning

- **gitleaks** — secret scan on PR/push (`security.yml`)
- **pip-audit** — dependency advisories from the lockfile
- **CodeQL** — enabled for public repositories
