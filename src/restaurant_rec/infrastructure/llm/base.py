"""LLM client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    role: str
    content: str


class LLMError(Exception):
    """Raised when the LLM provider returns an error."""


class LLMClient(ABC):
    """Provider-agnostic LLM completion interface."""

    @abstractmethod
    def complete(self, messages: list[Message], *, json_mode: bool = True) -> str:
        """Return the assistant message content."""

    @property
    def call_count(self) -> int:
        """Number of API calls made (for tests)."""
        return 0
