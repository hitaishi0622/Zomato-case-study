"""LLM ranking and explanation over filtered candidates."""

from __future__ import annotations

import logging
import time

from restaurant_rec.config.settings import Settings, get_settings
from restaurant_rec.domain.models import Recommendation, RecommendationMetadata, RecommendationResult
from restaurant_rec.domain.preferences import UserPreferences
from restaurant_rec.infrastructure.llm.base import LLMClient, LLMError
from restaurant_rec.infrastructure.llm.factory import create_llm_client
from restaurant_rec.services.prompt_builder import PromptBuilder
from restaurant_rec.services.response_parser import ResponseParseError, parse_llm_response
from restaurant_rec.services.validator import RecommendationValidator

logger = logging.getLogger(__name__)

FALLBACK_EXPLANATION = "Top pick by rating (LLM unavailable)."


class RecommendationEngine:
    """Call LLM to rank/explain candidates with retry, validation, and fallback."""

    def __init__(
        self,
        settings: Settings | None = None,
        llm_client: LLMClient | None = None,
        prompt_builder: PromptBuilder | None = None,
        validator: RecommendationValidator | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._llm = llm_client or create_llm_client(self._settings)
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._validator = validator or RecommendationValidator()

    def generate(
        self,
        preferences: UserPreferences,
        candidates: list,
        *,
        candidate_count: int | None = None,
    ) -> RecommendationResult:
        """
        Rank candidates via LLM and return validated recommendations.

        Falls back to top-3 by rating if LLM or validation fails twice.
        """
        from restaurant_rec.domain.models import Restaurant

        if not candidates:
            raise ValueError("generate() requires at least one candidate")

        if not all(isinstance(c, Restaurant) for c in candidates):
            raise TypeError("candidates must be a list of Restaurant")

        max_rec = self._settings.max_recommendations
        llm_calls = 0
        validation_drops = 0

        for attempt, strict in enumerate((False, True)):
            messages = self._prompt_builder.build(
                preferences,
                candidates,
                max_recommendations=max_rec,
                strict=strict,
            )
            start = time.perf_counter()
            try:
                raw = self._llm.complete(messages, json_mode=True)
                llm_calls += 1
            except LLMError as exc:
                logger.warning("LLM call failed (attempt %s): %s", attempt + 1, exc)
                if attempt == 1:
                    return self._rating_fallback(
                        candidates,
                        candidate_count=candidate_count,
                        llm_ms=(time.perf_counter() - start) * 1000,
                        llm_calls=llm_calls,
                    )
                continue

            llm_ms = (time.perf_counter() - start) * 1000
            try:
                parsed = parse_llm_response(raw)
            except ResponseParseError as exc:
                logger.warning("Parse failed (attempt %s): %s", attempt + 1, exc)
                if attempt == 1:
                    return self._rating_fallback(
                        candidates,
                        candidate_count=candidate_count,
                        llm_ms=llm_ms,
                        llm_calls=llm_calls,
                    )
                continue

            validation = self._validator.validate(parsed, candidates, max_recommendations=max_rec)
            validation_drops = validation.dropped_invalid_ids

            if validation.recommendations:
                logger.info(
                    "LLM recommendations: count=%s, llm_ms=%.0f, drops=%s",
                    len(validation.recommendations),
                    llm_ms,
                    validation_drops,
                )
                return RecommendationResult(
                    recommendations=validation.recommendations,
                    summary=validation.summary,
                    metadata=RecommendationMetadata(
                        candidate_count=candidate_count or len(candidates),
                        llm_ms=llm_ms,
                        llm_calls=llm_calls,
                        validation_drops=validation_drops,
                        degraded=False,
                    ),
                )

            logger.warning("Validation yielded zero recommendations (attempt %s)", attempt + 1)

        return self._rating_fallback(
            candidates,
            candidate_count=candidate_count,
            llm_calls=llm_calls,
            validation_drops=validation_drops,
        )

    def _rating_fallback(
        self,
        candidates: list,
        *,
        candidate_count: int | None = None,
        llm_ms: float | None = None,
        llm_calls: int = 0,
        validation_drops: int = 0,
    ) -> RecommendationResult:
        """Return top 3 by rating without LLM explanations."""
        sorted_candidates = sorted(
            candidates,
            key=lambda r: (r.rating, r.votes or 0),
            reverse=True,
        )[:3]
        recommendations = [
            Recommendation(
                restaurant=r,
                rank=i,
                explanation=FALLBACK_EXPLANATION,
            )
            for i, r in enumerate(sorted_candidates, start=1)
        ]
        logger.info("Using rating-only fallback (%s restaurants)", len(recommendations))
        return RecommendationResult(
            recommendations=recommendations,
            summary="Showing top-rated matches (AI explanations unavailable).",
            metadata=RecommendationMetadata(
                candidate_count=candidate_count or len(candidates),
                llm_ms=llm_ms,
                llm_calls=llm_calls,
                validation_drops=validation_drops,
                degraded=True,
            ),
        )
