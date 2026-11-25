"""Groq chat model, resolved per session and cached per distinct key."""

import logging
import threading
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from functools import lru_cache
from typing import Any

from langchain_groq import ChatGroq

from src.config.session import require, resolve_groq_api_key
from src.config.settings import (
    GROQ_MAX_COMPLETION_TOKENS,
    GROQ_MAX_RETRIES,
    GROQ_MODEL,
    GROQ_RETRY_BASE_SECONDS,
)

logger = logging.getLogger(__name__)

# A single-process gate prevents simultaneous requests from this app instance
# from creating avoidable TPM bursts against the shared Groq account.
_groq_call_lock = threading.Lock()


@lru_cache(maxsize=8)
def _build_llm(model: str, api_key: str) -> ChatGroq:
    return ChatGroq(
        model=model,
        api_key=api_key,
        max_tokens=GROQ_MAX_COMPLETION_TOKENS,
    )


def _retry_after_seconds(error: Exception) -> float | None:
    """Read Groq's Retry-After header when the client exposes its response."""
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", {}) or {}
    value = headers.get("retry-after") or headers.get("Retry-After")
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        try:
            when = parsedate_to_datetime(str(value))
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None


def invoke_llm(messages: Any, *, max_tokens: int | None = None):
    """Invoke Groq with bounded output, serialized calls and finite 429 retries."""
    llm = get_llm()
    if max_tokens is not None:
        llm = llm.bind(max_tokens=min(max_tokens, GROQ_MAX_COMPLETION_TOKENS))

    with _groq_call_lock:
        for attempt in range(GROQ_MAX_RETRIES + 1):
            try:
                return llm.invoke(messages)
            except Exception as error:
                status = getattr(error, "status_code", None)
                response = getattr(error, "response", None)
                status = status or getattr(response, "status_code", None)
                if status != 429 or attempt >= GROQ_MAX_RETRIES:
                    raise
                delay = _retry_after_seconds(error)
                if delay is None:
                    delay = GROQ_RETRY_BASE_SECONDS * (2 ** attempt)
                logger.warning(
                    "Groq rate limit (429); retry %d/%d in %.2fs",
                    attempt + 1, GROQ_MAX_RETRIES, delay,
                )
                time.sleep(delay)
        raise RuntimeError("Groq request retry loop ended unexpectedly")


def get_llm() -> ChatGroq:
    """
    The key comes from the current session if one supplied it, otherwise
    from the server's .env. One client is reused per distinct key.
    """

    require("GROQ_API_KEY")

    return _build_llm(GROQ_MODEL, resolve_groq_api_key())
