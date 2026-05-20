"""Orchestrate the recommendation workflow."""

from __future__ import annotations

import logging
import time

from restaurant_rec.config.settings import Settings, get_settings
from restaurant_rec.domain.filter_results import FilterResult, NoMatchResult
from restaurant_rec.domain.models import RecommendationResult
from restaurant_rec.domain.preferences import UserPreferences
from restaurant_rec.infrastructure import RestaurantRepository
from restaurant_rec.services import FilterService, RecommendationEngine

logger = logging.getLogger(__name__)


class RecommendationOrchestrator:
    """Full workflow orchestration from preferences to final recommendations."""

    def __init__(
        self,
        settings: Settings | None = None,
        repository: RestaurantRepository | None = None,
        filter_service: FilterService | None = None,
        recommendation_engine: RecommendationEngine | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._repository = repository
        self._filter_service = filter_service or FilterService(self._settings)
        self._recommendation_engine = recommendation_engine or RecommendationEngine(settings=self._settings)

    def recommend(
        self,
        preferences: UserPreferences,
        *,
        refresh: bool = False,
    ) -> RecommendationResult | NoMatchResult:
        """Filter restaurants and rank/explain them with the LLM."""
        repository = self._repository
        if refresh or repository is None:
            repository = RestaurantRepository.from_settings(self._settings, refresh=refresh)

        start = time.perf_counter()
        filter_outcome = self._filter_service.apply(
            repository.dataframe,
            preferences,
            available_cities=repository.distinct_cities(),
        )
        filter_ms = (time.perf_counter() - start) * 1000

        if isinstance(filter_outcome, NoMatchResult):
            return filter_outcome

        result = self._recommendation_engine.generate(
            preferences,
            filter_outcome.candidates,
            candidate_count=filter_outcome.total_matched,
        )

        result = result.model_copy(
            update={
                "metadata": result.metadata.model_copy(update={"filter_ms": filter_ms})
            }
        )
        logger.info(
            "Recommendation completed: candidates=%s, llm_calls=%s, filter_ms=%.0f",
            filter_outcome.total_matched,
            result.metadata.llm_calls,
            filter_ms,
        )
        return result
