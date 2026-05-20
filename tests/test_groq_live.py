"""Live Groq API integration test (requires saved .env with GROQ_API_KEY or LLM_API_KEY)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from restaurant_rec.config.settings import clear_settings_cache, get_settings
from restaurant_rec.domain.preferences import Budget, UserPreferences
from restaurant_rec.infrastructure import RestaurantRepository
from restaurant_rec.infrastructure.llm.groq_client import resolve_groq_api_key
from restaurant_rec.services import FilterService, RecommendationEngine


def _api_key_configured() -> bool:
    clear_settings_cache()
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.is_file() or env_path.stat().st_size == 0:
        return bool(os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY"))
    settings = get_settings()
    try:
        resolve_groq_api_key(settings)
        return True
    except Exception:
        return False


@pytest.mark.groq_live
def test_live_groq_recommendation() -> None:
    """End-to-end filter + Groq LLM on cached Bangalore data."""
    if not _api_key_configured():
        pytest.skip(
            "Groq API key not found. Save .env with GROQ_API_KEY=... or LLM_API_KEY=... "
            f"(file size: {(Path(__file__).parents[1] / '.env').stat().st_size if (Path(__file__).parents[1] / '.env').exists() else 0} bytes)"
        )

    clear_settings_cache()
    settings = get_settings()
    cache = settings.data_cache_path_resolved
    if not cache.exists():
        pytest.skip("Run: python -m restaurant_rec.main --refresh-data")

    repo = RestaurantRepository.from_settings(settings)
    prefs = UserPreferences(
        location="bangalore",
        budget=Budget.MEDIUM,
        cuisine="italian",
        min_rating=4.0,
        extras="family-friendly",
    )
    filtered = FilterService(settings).apply(
        repo.dataframe, prefs, available_cities=repo.distinct_cities()
    )
    from restaurant_rec.domain.filter_results import FilterResult

    assert isinstance(filtered, FilterResult)
    assert len(filtered.candidates) >= 1

    result = RecommendationEngine(settings=settings).generate(
        prefs,
        filtered.candidates,
        candidate_count=filtered.total_matched,
    )

    assert len(result.recommendations) >= 1
    assert result.recommendations[0].explanation
    assert not result.metadata.degraded
    assert result.metadata.llm_calls >= 1
    # Facts must come from dataset
    first = result.recommendations[0]
    assert first.restaurant.id in {c.id for c in filtered.candidates}
