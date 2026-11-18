"""Typed application errors mapped to Thai UI string keys (never raw tracebacks)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ErrorInfo:
    """UI-facing error payload."""

    code: str
    string_key: str
    hint_key: str | None = None
    details: dict[str, Any] | None = None


class AppError(Exception):
    """Base error that carries a stable code + i18n keys."""

    code: str = "error.generic"
    string_key: str = "error.generic"
    hint_key: str | None = "error.hint.retry"

    def __init__(self, message: str = "", *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message or self.code)
        self.details = details or {}

    def to_info(self) -> ErrorInfo:
        return ErrorInfo(
            code=self.code,
            string_key=self.string_key,
            hint_key=self.hint_key,
            details=dict(self.details),
        )


class MissingApiKeyError(AppError):
    code = "error.no_api_key"
    string_key = "error.no_api_key"
    hint_key = "error.hint.add_api_key"


class MissingModelConfigError(AppError):
    code = "error.missing_model_config"
    string_key = "error.missing_model_config"
    hint_key = "error.hint.set_models"


class RateLimitMinuteError(AppError):
    code = "error.rate_limit_minute"
    string_key = "error.rate_limit_minute"
    hint_key = "error.hint.wait_retry"


class RateLimitDayError(AppError):
    code = "error.rate_limit_day"
    string_key = "error.rate_limit_day"
    hint_key = "error.hint.wait_day"


class LlmTransportError(AppError):
    code = "error.llm_transport"
    string_key = "error.llm_transport"
    hint_key = "error.hint.check_network"


class LlmResponseError(AppError):
    code = "error.llm_response"
    string_key = "error.llm_response"
    hint_key = "error.hint.retry"


class PersonaLoadError(AppError):
    code = "error.persona_load"
    string_key = "error.persona_load"
    hint_key = "error.hint.fix_persona"


class KnowledgeNotFoundError(AppError):
    """Strict answer_mode short-circuit (no LLM call)."""

    code = "error.not_found_strict"
    string_key = "error.not_found_strict"
    hint_key = "error.hint.add_knowledge"


def to_error_info(exc: BaseException) -> ErrorInfo:
    if isinstance(exc, AppError):
        return exc.to_info()
    return ErrorInfo(code="error.generic", string_key="error.generic", hint_key="error.hint.retry")
