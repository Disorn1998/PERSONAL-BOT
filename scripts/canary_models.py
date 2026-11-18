#!/usr/bin/env python3
"""Weekly canary — GET /models only; never chat/completions (§16.7).

Compares ``GROQ_MODEL_PRIMARY`` / ``GROQ_MODEL_FALLBACK`` from ``.env.example``
against the live catalogue. Opens at most one open GitHub issue (no duplicates).

Env:
  GROQ_API_KEY (required) — maintainer secret
  GROQ_BASE_URL (optional) — default from .env.example / Groq
  GITHUB_TOKEN + GITHUB_REPOSITORY — for issue creation when CANARY_OPEN_ISSUES=1
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from persona_bot.security import hostname_in_allowlist, url_hostname  # noqa: E402

ENV_EXAMPLE = ROOT / ".env.example"
ISSUE_MARKER = "<!-- persona-bot-canary-models -->"
# Hostnames we may call for canary (exact match via urlparse — not substring).
_CANARY_HOST_ALLOWLIST = (
    "api.groq.com",
    "127.0.0.1",
    "localhost",
    "fake-groq",
)


def _parse_env_example(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        out[key.strip()] = value.strip()
    return out


def _get_models(base_url: str, api_key: str) -> list[str]:
    url = base_url.rstrip("/") + "/models"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "persona-bot-canary/1.0",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 — fixed https/http API
        payload = json.loads(resp.read().decode("utf-8"))
    data = payload.get("data") or []
    return [str(item.get("id") or "") for item in data if isinstance(item, dict)]


def _find_open_canary_issue(repo: str, token: str) -> int | None:
    url = f"https://api.github.com/repos/{repo}/issues?state=open&per_page=50"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "persona-bot-canary/1.0",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        issues = json.loads(resp.read().decode("utf-8"))
    for issue in issues:
        body = str(issue.get("body") or "")
        title = str(issue.get("title") or "")
        if ISSUE_MARKER in body or title.startswith("[canary] Groq models"):
            return int(issue["number"])
    return None


def _open_issue(repo: str, token: str, title: str, body: str) -> None:
    url = f"https://api.github.com/repos/{repo}/issues"
    payload = json.dumps({"title": title, "body": body}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "persona-bot-canary/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        created = json.loads(resp.read().decode("utf-8"))
    print(f"opened issue #{created.get('number')}", flush=True)


def main() -> int:
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        print("GROQ_API_KEY missing — skip canary (maintainer secret).", flush=True)
        return 0

    example = _parse_env_example(ENV_EXAMPLE)
    primary = example.get("GROQ_MODEL_PRIMARY", "").strip()
    fallback = example.get("GROQ_MODEL_FALLBACK", "").strip()
    base = (
        os.environ.get("GROQ_BASE_URL", "").strip()
        or example.get("GROQ_BASE_URL", "").strip()
        or "https://api.groq.com/openai/v1"
    )
    if not primary:
        print("GROQ_MODEL_PRIMARY missing from .env.example", file=sys.stderr)
        return 2

    host = url_hostname(base)
    if host is None or not hostname_in_allowlist(base, _CANARY_HOST_ALLOWLIST):
        print(
            f"GROQ_BASE_URL hostname not allowlisted: {host!r} (urlparse check)",
            file=sys.stderr,
        )
        return 2
    print(f"canary base host={host}")

    try:
        ids = _get_models(base, api_key)
    except urllib.error.HTTPError as exc:
        print(f"GET /models failed: HTTP {exc.code}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"GET /models failed: {exc}", file=sys.stderr)
        return 1

    missing = [m for m in (primary, fallback) if m and m not in ids]
    print(f"catalogue_size={len(ids)} primary={primary} fallback={fallback}")
    if not missing:
        print("canary ok — .env.example models present in GET /models")
        return 0

    msg = (
        f"Canary failed: models missing from GET /models: {missing}\n"
        f"base={base} catalogue_size={len(ids)}"
    )
    print(msg, file=sys.stderr)

    if os.environ.get("CANARY_OPEN_ISSUES", "").strip() == "1":
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
        if token and repo:
            existing = _find_open_canary_issue(repo, token)
            if existing is not None:
                print(f"open canary issue already exists: #{existing} — no duplicate")
            else:
                body = (
                    f"{ISSUE_MARKER}\n"
                    f"Automated weekly canary (`scripts/canary_models.py`).\n\n"
                    f"- Missing: `{', '.join(missing)}`\n"
                    f"- Base URL: `{base}`\n"
                    f"- Action: update `.env.example` model IDs after checking "
                    f"https://console.groq.com/docs/deprecations\n\n"
                    f"**Constraint:** this canary only calls `GET /models` "
                    f"(never `chat/completions`)."
                )
                _open_issue(
                    repo,
                    token,
                    "[canary] Groq models missing from GET /models",
                    body,
                )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
