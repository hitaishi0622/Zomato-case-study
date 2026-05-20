"""Factory for LLM client instances."""

from __future__ import annotations

from restaurant_rec.config.settings import Settings
from restaurant_rec.infrastructure.llm.base import LLMClient, LLMError
from restaurant_rec.infrastructure.llm.groq_client import GroqClient


def create_llm_client(settings: Settings) -> LLMClient:
    """Create an LLM client for the configured provider."""
    provider = settings.llm_provider
    if provider == "groq":
        return GroqClient(settings)
    raise LLMError(
        f"Unsupported LLM provider '{provider}'. This project uses Groq by default; set LLM_PROVIDER=groq."
    )
