"""Unit tests for canary parsing + fake Groq server (no real network to Groq)."""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from app.security import hostname_equals

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, rel: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_parse_env_example_models() -> None:
    canary = _load("canary_models", "scripts/canary_models.py")
    values = canary._parse_env_example(ROOT / ".env.example")
    assert values["GROQ_MODEL_PRIMARY"]
    assert values["GROQ_MODEL_FALLBACK"]
    # Hostname equality — never substring ``in`` (CodeQL incomplete URL sanitization).
    assert hostname_equals(values["GROQ_BASE_URL"], "api.groq.com")


def test_fake_groq_models_endpoint() -> None:
    fake = _load("fake_groq_server", "scripts/fake_groq_server.py")
    server = ThreadingHTTPServer(("127.0.0.1", 0), fake.Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/v1/models", timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        ids = {item["id"] for item in payload["data"]}
        assert "openai/gpt-oss-120b" in ids
        assert "openai/gpt-oss-20b" in ids
    finally:
        server.shutdown()
