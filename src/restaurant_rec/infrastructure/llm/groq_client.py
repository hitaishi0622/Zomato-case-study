"""Groq LLM client implementation."""

from __future__ import annotations

import logging
import os

from groq import Groq

from restaurant_rec.config.settings import Settings
from restaurant_rec.infrastructure.llm.base import LLMClient, LLMError, Message

logger = logging.getLogger(__name__)


def resolve_groq_api_key(settings: Settings) -> str:
    """Resolve API key from settings or environment."""
    key = settings.llm_api_key or os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")
    if not key:
        raise LLMError(
            "Groq API key not configured. Set GROQ_API_KEY or LLM_API_KEY in your environment."
        )
    return key


class GroqClient(LLMClient):
    """Call Groq chat completions API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = Groq(api_key=resolve_groq_api_key(settings))
        self._call_count = 0

    @property
    def call_count(self) -> int:
        return self._call_count

    def complete(self, messages: list[Message], *, json_mode: bool = True) -> str:
        payload = [{"role": m.role, "content": m.content} for m in messages]
        kwargs: dict = {
            "model": self._settings.llm_model,
            "messages": payload,
            "temperature": self._settings.llm_temperature,
            "timeout": float(self._settings.llm_timeout_sec),
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            self._call_count += 1
            response = self._client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            if not content:
                raise LLMError("Groq returned empty content")
            return content
        except LLMError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Groq API call failed")
            raise LLMError(f"Groq API error: {exc}") from exc
