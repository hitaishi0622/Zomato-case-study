"""User preference input models."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator

# City aliases for normalized matching (extend as needed)
CITY_ALIASES: dict[str, str] = {
    "bengaluru": "bangalore",
    "bangalore": "bangalore",
    "new delhi": "new delhi",
    "delhi": "new delhi",
    "ncr": "new delhi",
}


class Budget(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def normalize_location(location: str) -> str:
    """Normalize and resolve city aliases for filtering."""
    key = location.strip().lower()
    if not key:
        return key
    return CITY_ALIASES.get(key, key)


class UserPreferences(BaseModel):
    """Structured user input for restaurant search."""

    location: str = Field(description="City or locality to search in")
    budget: Budget
    cuisine: str | None = Field(default=None, description="Cuisine type; omit to match any")
    min_rating: float = Field(default=0.0, ge=0.0, le=5.0)
    extras: str | None = Field(
        default=None,
        description="Free-text preferences (used by LLM in Phase 3+, not filtering)",
    )

    model_config = {"frozen": True}

    @field_validator("location", mode="before")
    @classmethod
    def validate_location(cls, value: object) -> str:
        if value is None:
            raise ValueError("location is required")
        text = str(value).strip()
        if not text:
            raise ValueError("location is required")
        return normalize_location(text)

    @field_validator("cuisine", "extras", mode="before")
    @classmethod
    def strip_optional_text(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("budget", mode="before")
    @classmethod
    def normalize_budget(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value
