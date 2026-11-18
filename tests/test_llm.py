"""LLM client with mocked OpenAI stream — never calls real Groq."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from app.config import Settings
from app.errors import MissingApiKeyError, MissingModelConfigError
from app.llm import SDK_MAX_RETRIES, LlmClient, StreamResult, build_client
from openai import APIStatusError


class _FakeRawResponse:
    def __init__(self, headers: dict[str, str], stream: list[Any]) -> None:
        self.headers = headers
        self._stream = stream

    def parse(self) -> list[Any]:
        return self._stream


class _FakeCompletions:
    def __init__(self, handler: Any) -> None:
        self._handler = handler
        self.with_raw_response = self

    def create(self, **kwargs: Any) -> _FakeRawResponse:
        return self._handler(**kwargs)


class _FakeOpenAI:
    def __init__(self, handler: Any) -> None:
        self.chat = SimpleNamespace(completions=_FakeCompletions(handler))


def _chunk(text: str | None, *, finish: str | None = None, usage: Any = None) -> Any:
    delta = SimpleNamespace(content=text)
    choice = SimpleNamespace(delta=delta, finish_reason=finish)
    has_choice = text is not None or finish is not None
    return SimpleNamespace(choices=[choice] if has_choice else [], usage=usage)


def _status_error(status: int, message: str, headers: dict[str, str]) -> APIStatusError:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(status, headers=headers, request=request)
    return APIStatusError(message, response=response, body={"error": {"message": message}})


def test_sdk_max_retries_is_zero() -> None:
    assert SDK_MAX_RETRIES == 0


def test_build_client_requires_key() -> None:
    with pytest.raises(MissingApiKeyError):
        build_client(api_key="", base_url="https://example.test", timeout=5)


def test_stream_chat_yields_text_and_fills_result() -> None:
    usage = SimpleNamespace(
        prompt_tokens=10,
        completion_tokens=3,
        total_tokens=13,
        prompt_tokens_details=SimpleNamespace(cached_tokens=4),
    )
    stream = [
        _chunk("สวัสดี"),
        _chunk(" โลก", finish="stop"),
        SimpleNamespace(choices=[], usage=usage),
    ]

    def handler(**kwargs: Any) -> _FakeRawResponse:
        assert kwargs["model"] == "model-a"
        assert kwargs["stream"] is True
        assert kwargs["stream_options"] == {"include_usage": True}
        return _FakeRawResponse(
            {
                "x-ratelimit-remaining-requests": "99",
                "x-ratelimit-remaining-tokens": "1000",
            },
            stream,
        )

    settings = Settings(
        GROQ_MODEL_PRIMARY="model-a",
        GROQ_MODEL_FALLBACK="model-b",
        GROQ_API_KEY="test-key",
    )
    client = LlmClient(settings=settings, api_key="test-key", client=_FakeOpenAI(handler))  # type: ignore[arg-type]
    result = StreamResult()
    text = "".join(client.stream_chat([{"role": "user", "content": "hi"}], result=result))
    assert text == "สวัสดี โลก"
    assert result.text == text
    assert result.model == "model-a"
    assert result.finish_reason == "stop"
    assert result.usage.cached_tokens == 4
    assert result.rate_limit.remaining_requests == 99
    assert result.used_fallback is False


def test_missing_model_config() -> None:
    settings = Settings(GROQ_MODEL_PRIMARY="", GROQ_API_KEY="x")

    def handler(**kwargs: Any) -> _FakeRawResponse:
        raise AssertionError("should not call API")

    client = LlmClient(
        settings=settings,
        api_key="x",
        client=_FakeOpenAI(handler),  # type: ignore[arg-type]
    )
    with pytest.raises(MissingModelConfigError):
        list(client.stream_chat([{"role": "user", "content": "hi"}]))


def test_minute_rate_limit_falls_back() -> None:
    calls: list[str] = []

    def handler(**kwargs: Any) -> _FakeRawResponse:
        model = str(kwargs["model"])
        calls.append(model)
        if model == "model-a":
            raise _status_error(
                429,
                "Rate limit reached for tokens per minute (TPM)",
                {
                    "x-ratelimit-remaining-tokens": "0",
                    "x-ratelimit-remaining-requests": "50",
                },
            )
        usage = SimpleNamespace(
            prompt_tokens=1,
            completion_tokens=1,
            total_tokens=2,
            prompt_tokens_details=None,
        )
        return _FakeRawResponse(
            {"x-ratelimit-remaining-requests": "49"},
            [_chunk("ok", finish="stop"), SimpleNamespace(choices=[], usage=usage)],
        )

    settings = Settings(
        GROQ_MODEL_PRIMARY="model-a",
        GROQ_MODEL_FALLBACK="model-b",
        GROQ_API_KEY="test-key",
    )
    client = LlmClient(settings=settings, api_key="test-key", client=_FakeOpenAI(handler))  # type: ignore[arg-type]
    result = StreamResult()
    text = "".join(client.stream_chat([{"role": "user", "content": "hi"}], result=result))
    assert text == "ok"
    assert calls == ["model-a", "model-b"]
    assert result.used_fallback is True
    assert result.model == "model-b"
