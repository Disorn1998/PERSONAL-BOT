#!/usr/bin/env python3
"""Minimal OpenAI-compatible fake Groq for Docker/CI e2e.

Serves:
  GET  /v1/models
  POST /v1/chat/completions  (non-streaming JSON; never calls real Groq)

Usage::

    python scripts/fake_groq_server.py --port 8080
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODELS = [
    {"id": "openai/gpt-oss-120b", "object": "model", "owned_by": "fake"},
    {"id": "openai/gpt-oss-20b", "object": "model", "owned_by": "fake"},
]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return

    def _json(self, code: int, payload: object) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path in {"/v1/models", "/models"}:
            self._json(200, {"object": "list", "data": MODELS})
            return
        if path in {"/health", "/"}:
            self._json(200, {"ok": True})
            return
        self._json(404, {"error": {"message": f"not found: {path}"}})

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            req = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            req = {}
        if path in {"/v1/chat/completions", "/chat/completions"}:
            model = str(req.get("model") or "fake-model")
            # Non-streaming response is enough for health/smoke; Streamlit may stream —
            # clients that request stream=true still accept a full JSON body from some SDKs,
            # but we prefer a tiny SSE payload when stream is true.
            if req.get("stream"):
                text = (
                    "data: "
                    + json.dumps(
                        {
                            "id": "fake-1",
                            "object": "chat.completion.chunk",
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"role": "assistant", "content": "สวัสดีจาก fake Groq"},
                                    "finish_reason": None,
                                }
                            ],
                        }
                    )
                    + "\n\n"
                    "data: "
                    + json.dumps(
                        {
                            "id": "fake-1",
                            "object": "chat.completion.chunk",
                            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                            "usage": {
                                "prompt_tokens": 1,
                                "completion_tokens": 1,
                                "total_tokens": 2,
                            },
                        }
                    )
                    + "\n\n"
                    "data: [DONE]\n\n"
                )
                data = text.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            self._json(
                200,
                {
                    "id": "fake-1",
                    "object": "chat.completion",
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "สวัสดีจาก fake Groq",
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 1,
                        "completion_tokens": 1,
                        "total_tokens": 2,
                    },
                },
            )
            return
        self._json(404, {"error": {"message": f"not found: {path}"}})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"fake-groq listening on {args.host}:{args.port}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
