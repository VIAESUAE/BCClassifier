from __future__ import annotations

from contextvars import ContextVar
from typing import Optional

from app.config import get_settings

_override_api_key: ContextVar[Optional[str]] = ContextVar("override_api_key", default=None)
_override_base_url: ContextVar[Optional[str]] = ContextVar("override_base_url", default=None)
_override_model: ContextVar[Optional[str]] = ContextVar("override_model", default=None)


def set_request_llm_overrides(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> None:
    _override_api_key.set((api_key or "").strip() or None)
    _override_base_url.set((base_url or "").strip() or None)
    _override_model.set((model or "").strip() or None)


def effective_api_key() -> str:
    return _override_api_key.get() or get_settings().openai_api_key or ""


def effective_base_url() -> str:
    return _override_base_url.get() or get_settings().openai_base_url


def effective_model() -> str:
    return _override_model.get() or get_settings().openai_model


def has_llm() -> bool:
    return bool(effective_api_key().strip())
