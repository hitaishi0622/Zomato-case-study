"""Build LLM prompts for restaurant ranking."""

from __future__ import annotations

import json

from restaurant_rec.domain.models import Restaurant
from restaurant_rec.domain.preferences import UserPreferences
from restaurant_rec.infrastructure.llm.base import Message

STRICT_REMINDER = (
    "CRITICAL: Respond with valid JSON only. Use ONLY restaurant ids from CANDIDATES. "
    "Do not invent restaurants. Every id must appear in the candidate list."
)


class PromptBuilder:
    """Construct system and user messages for the recommendation LLM."""

    def build(
        self,
        preferences: UserPreferences,
        candidates: list[Restaurant],
        *,
        max_recommendations: int,
        strict: bool = False,
    ) -> list[Message]:
        system = self._system_prompt(strict=strict)
        user = self._user_prompt(preferences, candidates, max_recommendations)
        return [Message(role="system", content=system), Message(role="user", content=user)]

    @staticmethod
    def _system_prompt(*, strict: bool) -> str:
        base = (
            "You are a restaurant recommendation assistant for Indian cities. "
            "You may ONLY recommend restaurants from the CANDIDATES list provided by the user. "
            "Never invent or rename restaurants. "
            "Return JSON matching this schema exactly:\n"
            "{\n"
            '  "summary": "short overview string",\n'
            '  "recommendations": [\n'
            '    {"id": "<candidate id>", "rank": 1, "explanation": "2-3 sentences"}\n'
            "  ]\n"
            "}\n"
            "Reference the user's preferences including extras when writing explanations. "
            "Order ranks from 1 (best) upward without duplicates."
        )
        if strict:
            return f"{base}\n\n{STRICT_REMINDER}"
        return base

    @staticmethod
    def _user_prompt(
        preferences: UserPreferences,
        candidates: list[Restaurant],
        max_recommendations: int,
    ) -> str:
        prefs_payload = {
            "location": preferences.location,
            "budget": preferences.budget.value,
            "cuisine": preferences.cuisine,
            "min_rating": preferences.min_rating,
            "extras": preferences.extras,
        }
        candidate_rows = [
            {
                "id": r.id,
                "name": r.name,
                "city": r.city,
                "locality": r.locality,
                "cuisines": r.cuisines,
                "rating": r.rating,
                "cost_for_two": r.cost_for_two,
                "votes": r.votes,
            }
            for r in candidates
        ]
        payload = {
            "preferences": prefs_payload,
            "max_recommendations": max_recommendations,
            "candidates": candidate_rows,
        }
        return (
            "Rank the best restaurants for these preferences. "
            "Use only the ids below.\n\n"
            f"{json.dumps(payload, indent=2)}"
        )
