# Security

- Bring your own Groq key (BYOK). Keys stay in session by default.
- Optional OS keyring (`PERSONA_BOT_REMEMBER_KEY=1`) stores the key **outside** `data/`.
- Never commit `.env` or anything under `data/`.
- Logs redact API-key-like strings (`app/security.py`).
- `APP_PASSWORD` is a simple local gate — **not** multi-user auth.
- Report vulnerabilities privately to the repository owner.
