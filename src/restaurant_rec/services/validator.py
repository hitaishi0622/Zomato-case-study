"""Validate LLM recommendations against candidate restaurants."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from restaurant_rec.domain.models import Recommendation, Restaurant
from restaurant_rec.services.response_parser import ParsedLLMResponse

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    recommendations: list[Recommendation]
    summary: str | None
    dropped_invalid_ids: int
    deduplicated_ids: int


class RecommendationValidator:
    """Ensure LLM output only references known candidates; facts come from dataset."""

    def validate(
        self,
        parsed: ParsedLLMResponse,
        candidates: list[Restaurant],
        *,
        max_recommendations: int,
    ) -> ValidationResult:
        by_id = {r.id: r for r in candidates}
        valid_ids = set(by_id.keys())

        seen_ids: set[str] = set()
        built: list[Recommendation] = []
        dropped = 0
        deduped = 0

        sorted_items = sorted(parsed.recommendations, key=lambda item: item.rank)
        for item in sorted_items:
            if item.id not in valid_ids:
                dropped += 1
                logger.warning("Dropping hallucinated or unknown id: %s", item.id)
                continue
            if item.id in seen_ids:
                deduped += 1
                continue
            seen_ids.add(item.id)
            restaurant = by_id[item.id]
            built.append(
                Recommendation(
                    restaurant=restaurant,
                    rank=len(built) + 1,
                    explanation=item.explanation.strip(),
                )
            )
            if len(built) >= max_recommendations:
                break

        return ValidationResult(
            recommendations=built,
            summary=parsed.summary,
            dropped_invalid_ids=dropped,
            deduplicated_ids=deduped,
        )
