"""Parse LLM JSON responses."""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError

_JSON_FENCE_PATTERN = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


class ParsedRecommendation(BaseModel):
    id: str
    rank: int = Field(ge=1)
    explanation: str


class ParsedLLMResponse(BaseModel):
    summary: str | None = None
    recommendations: list[ParsedRecommendation]


class ResponseParseError(Exception):
    """Raised when LLM output cannot be parsed as expected JSON."""


def extract_json_text(raw: str) -> str:
    """Strip markdown fences and surrounding whitespace from LLM output."""
    text = raw.strip()
    match = _JSON_FENCE_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return text


def parse_llm_response(raw: str) -> ParsedLLMResponse:
    """Parse and validate LLM JSON output."""
    text = extract_json_text(raw)
    try:
        data: Any = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ResponseParseError(f"Invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ResponseParseError("Expected JSON object at top level")

    try:
        return ParsedLLMResponse.model_validate(data)
    except ValidationError as exc:
        raise ResponseParseError(f"Schema validation failed: {exc}") from exc
