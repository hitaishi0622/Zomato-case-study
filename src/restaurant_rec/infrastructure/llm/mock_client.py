"""Mock LLM client for tests."""

from __future__ import annotations

import json

from restaurant_rec.infrastructure.llm.base import LLMClient, LLMError, Message


class MockLLMClient(LLMClient):
    """Returns a canned JSON response or raises on demand."""

    def __init__(
        self,
        response_json: dict | None = None,
        *,
        fail_times: int = 0,
        return_invalid_json: bool = False,
    ) -> None:
        self._response_json = response_json
        self._fail_times = fail_times
        self._return_invalid_json = return_invalid_json
        self._call_count = 0
        self.last_messages: list[Message] | None = None

    @property
    def call_count(self) -> int:
        return self._call_count

    def complete(self, messages: list[Message], *, json_mode: bool = True) -> str:
        self._call_count += 1
        self.last_messages = messages

        if self._fail_times >= self._call_count:
            raise LLMError("Mock LLM failure")

        if self._return_invalid_json:
            return "This is not JSON."

        if self._response_json is None:
            raise LLMError("MockLLMClient: no response_json configured")

        return json.dumps(self._response_json)
