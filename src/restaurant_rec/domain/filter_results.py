"""Filter operation outcomes."""

from __future__ import annotations

from pydantic import BaseModel, Field

from restaurant_rec.domain.models import Restaurant
from restaurant_rec.domain.preferences import UserPreferences


class FilterResult(BaseModel):
    """Successful filter with capped candidate restaurants."""

    candidates: list[Restaurant]
    total_matched: int = Field(description="Count before applying top-N cap")
    preferences: UserPreferences

    model_config = {"frozen": True}


class NoMatchResult(BaseModel):
    """No restaurants matched the given preferences."""

    preferences: UserPreferences
    hints: list[str] = Field(default_factory=list)

    model_config = {"frozen": True}
