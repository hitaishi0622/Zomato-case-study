"""Domain models for restaurant data."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Restaurant(BaseModel):
    """Normalized restaurant record used across the application."""

    id: str = Field(description="Stable restaurant identifier")
    name: str
    city: str
    locality: str | None = None
    cuisines: list[str] = Field(default_factory=list)
    rating: float = Field(ge=0.0, le=5.0)
    cost_for_two: float = Field(ge=0.0)
    votes: int | None = None
    raw: dict[str, Any] | None = Field(
        default=None,
        description="Optional extra fields from the source dataset",
    )

    model_config = {"frozen": True}


class Recommendation(BaseModel):
    """A ranked restaurant with an LLM-generated explanation."""

    restaurant: Restaurant
    rank: int = Field(ge=1)
    explanation: str

    model_config = {"frozen": True}


class RecommendationMetadata(BaseModel):
    """Timing and diagnostic metadata for a recommendation run."""

    candidate_count: int = 0
    filter_ms: float | None = None
    llm_ms: float | None = None
    llm_calls: int = 0
    validation_drops: int = 0
    degraded: bool = False

    model_config = {"frozen": True}


class RecommendationResult(BaseModel):
    """Successful LLM-backed recommendations."""

    recommendations: list[Recommendation]
    summary: str | None = None
    metadata: RecommendationMetadata = Field(default_factory=RecommendationMetadata)

    model_config = {"frozen": True}
