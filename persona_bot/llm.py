"""Groq chat via OpenAI-compatible SDK — streaming text only + StreamResult."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

from app.config import Settings, get_settings
from app.errors import (
    LlmResponseError,
    LlmTransportError,
    MissingApiKeyError,
    MissingModelConfigError,
    RateLimitDayError,
    RateLimitMinuteError,
)
from app.logging_setup import get_logger
from app.ratelimit import RateLimitInfo, classify_429, parse_rate_limit_headers
from app.security import safe_exception_message

logger = get_logger(__name__)

# App owns retries / fallback — disable SDK retries (F2).
SDK_MAX_RETRIES = 0


@dataclass(slots=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0


@dataclass(slots=True)
class StreamResult:
    """Filled when a stream ends (success or handled failure)."""

    model: str = ""
    usage: TokenUsage = field(default_factory=TokenUsage)
    finish_reason: str | None = None
    rate_limit: RateLimitInfo = field(default_factory=RateLimitInfo)
    used_fallback: bool = False
    text: str = ""
    error: str | None = None


class ChatClient(Protocol):
    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        result: StreamResult | None = None,
    ) -> Iterator[str]: ...


def build_client(
    *,
    api_key: str,
    base_url: str,
    timeout: float,
) -> OpenAI:
    if not api_key.strip():
        raise MissingApiKeyError()
    return OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
        max_retries=SDK_MAX_RETRIES,
    )


def _usage_from_chunk(usage_obj: Any) -> TokenUsage:
    if usage_obj is None:
        return TokenUsage()
    prompt = int(getattr(usage_obj, "prompt_tokens", 0) or 0)
    completion = int(getattr(usage_obj, "completion_tokens", 0) or 0)
    total = int(getattr(usage_obj, "total_tokens", 0) or (prompt + completion))
    cached = 0
    details = getattr(usage_obj, "prompt_tokens_details", None)
    if details is not None:
        cached = int(getattr(details, "cached_tokens", 0) or 0)
    return TokenUsage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=total,
        cached_tokens=cached,
    )


def _raise_for_status(exc: APIStatusError, *, api_key: str) -> None:
    raw_headers = getattr(exc, "headers", None) or {}
    headers: Mapping[str, str] = {str(k): str(v) for k, v in dict(raw_headers).items()}
    body = safe_exception_message(exc, api_key=api_key)
    if exc.status_code == 429:
        raise classify_429(headers=headers, body_text=body) from exc
    raise LlmResponseError(body, details={"status_code": exc.status_code}) from exc


class LlmClient:
    """Primary→fallback streaming chat. Yields text chunks only for ``st.write_stream``."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        api_key: str | None = None,
        client: OpenAI | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.api_key = (api_key if api_key is not None else self.settings.groq_api_key).strip()
        self._client = client or build_client(
            api_key=self.api_key,
            base_url=self.settings.groq_base_url,
            timeout=self.settings.llm_timeout_seconds,
        )

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        result: StreamResult | None = None,
    ) -> Iterator[str]:
        out = result if result is not None else StreamResult()
        try:
            primary, fallback = self.settings.require_models()
        except ValueError as exc:
            raise MissingModelConfigError(str(exc)) from exc

        models = [primary]
        if fallback and fallback != primary:
            models.append(fallback)

        last_error: BaseException | None = None
        for index, model in enumerate(models):
            used_fallback = index > 0
            try:
                yield from self._stream_one(
                    messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    result=out,
                    used_fallback=used_fallback,
                )
                return
            except RateLimitDayError as exc:
                out.error = safe_exception_message(exc, api_key=self.api_key)
                raise
            except RateLimitMinuteError as exc:
                last_error = exc
                out.error = safe_exception_message(exc, api_key=self.api_key)
                if index == 0 and len(models) > 1:
                    logger.warning("primary model rate-limited (minute); trying fallback")
                    continue
                raise
            except LlmTransportError as exc:
                last_error = exc
                out.error = safe_exception_message(exc, api_key=self.api_key)
                if index == 0 and len(models) > 1:
                    logger.warning("primary model transport error; trying fallback")
                    continue
                raise
            except (APIConnectionError, APITimeoutError) as exc:
                wrapped = LlmTransportError(safe_exception_message(exc, api_key=self.api_key))
                last_error = wrapped
                out.error = str(wrapped)
                if index == 0 and len(models) > 1:
                    logger.warning("primary model transport error; trying fallback")
                    continue
                raise wrapped from exc

        if last_error is not None:
            raise last_error

    def _stream_one(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str,
        temperature: float,
        max_tokens: int | None,
        result: StreamResult,
        used_fallback: bool,
    ) -> Iterator[str]:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        parts: list[str] = []
        result.model = model
        result.used_fallback = used_fallback

        try:
            # with_raw_response exposes headers; parse() returns the stream.
            # TODO(verify): confirm Groq returns x-ratelimit-* on streaming create.
            raw = self._client.chat.completions.with_raw_response.create(**kwargs)
            result.rate_limit = parse_rate_limit_headers(dict(raw.headers))
            stream = raw.parse()
            for chunk in stream:
                usage = getattr(chunk, "usage", None)
                if usage is not None:
                    result.usage = _usage_from_chunk(usage)
                choices = getattr(chunk, "choices", None) or []
                if not choices:
                    continue
                choice = choices[0]
                finish = getattr(choice, "finish_reason", None)
                if finish:
                    result.finish_reason = finish
                delta = getattr(choice, "delta", None)
                content = getattr(delta, "content", None) if delta is not None else None
                if content:
                    parts.append(content)
                    yield content
        except APIStatusError as exc:
            _raise_for_status(exc, api_key=self.api_key)
        except (APIConnectionError, APITimeoutError) as exc:
            raise LlmTransportError(safe_exception_message(exc, api_key=self.api_key)) from exc

        result.text = "".join(parts)
