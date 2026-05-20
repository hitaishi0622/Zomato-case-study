"""Tests for filter service (Phase 2)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from restaurant_rec.domain.filter_results import FilterResult, NoMatchResult
from restaurant_rec.domain.preferences import Budget, UserPreferences
from restaurant_rec.services.budget_tiers import load_budget_tiers
from restaurant_rec.services.filter_service import FilterService


@pytest.fixture
def budget_tiers() -> dict:
    return {
        Budget.LOW: (0, 300),
        Budget.MEDIUM: (301, 500),
        Budget.HIGH: (501, 999999),
    }


@pytest.fixture
def filter_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "restaurant_id": "r_blr_italian",
                "name": "italian kitchen",
                "city": "bangalore",
                "locality": "indiranagar",
                "cuisines_str": "italian, pizza",
                "rating": 4.5,
                "cost_for_two": 450,
                "votes": 200,
            },
            {
                "restaurant_id": "r_blr_chinese",
                "name": "dragon wok",
                "city": "bangalore",
                "locality": "koramangala",
                "cuisines_str": "chinese, thai",
                "rating": 4.0,
                "cost_for_two": 350,
                "votes": 150,
            },
            {
                "restaurant_id": "r_blr_cheap",
                "name": "budget bites",
                "city": "bangalore",
                "locality": "btm",
                "cuisines_str": "italian",
                "rating": 3.2,
                "cost_for_two": 200,
                "votes": 50,
            },
            {
                "restaurant_id": "r_delhi_chinese",
                "name": "delhi dumplings",
                "city": "new delhi",
                "locality": "connaught place",
                "cuisines_str": "chinese, momos",
                "rating": 4.3,
                "cost_for_two": 400,
                "votes": 180,
            },
            {
                "restaurant_id": "r_blr_expensive",
                "name": "fine dine",
                "city": "bangalore",
                "locality": "mg road",
                "cuisines_str": "italian, continental",
                "rating": 4.8,
                "cost_for_two": 900,
                "votes": 300,
            },
        ]
    )


@pytest.fixture
def filter_service(budget_tiers: dict) -> FilterService:
    from restaurant_rec.config.settings import Settings

    settings = Settings(max_candidates_for_llm=15)
    return FilterService(settings=settings, budget_tiers=budget_tiers)


def test_filter_location_excludes_other_cities(filter_service: FilterService, filter_df: pd.DataFrame) -> None:
    prefs = UserPreferences(location="delhi", budget=Budget.MEDIUM, cuisine="chinese", min_rating=4.0)
    result = filter_service.apply(filter_df, prefs)
    assert isinstance(result, FilterResult)
    cities = {r.city for r in result.candidates}
    assert cities == {"new delhi"}
    assert all(r.city != "bangalore" for r in result.candidates)


def test_filter_location_case_insensitive(filter_service: FilterService, filter_df: pd.DataFrame) -> None:
    lower = UserPreferences(location="bangalore", budget=Budget.MEDIUM, min_rating=0.0)
    upper = UserPreferences(location="Bangalore", budget=Budget.MEDIUM, min_rating=0.0)
    r1 = filter_service.apply(filter_df, lower)
    r2 = filter_service.apply(filter_df, upper)
    assert isinstance(r1, FilterResult) and isinstance(r2, FilterResult)
    assert r1.total_matched == r2.total_matched


def test_filter_budget_medium(filter_service: FilterService, filter_df: pd.DataFrame) -> None:
    prefs = UserPreferences(location="bangalore", budget=Budget.MEDIUM, min_rating=0.0)
    result = filter_service.apply(filter_df, prefs)
    assert isinstance(result, FilterResult)
    for r in result.candidates:
        assert 301 <= r.cost_for_two <= 500


def test_filter_min_rating(filter_service: FilterService, filter_df: pd.DataFrame) -> None:
    prefs = UserPreferences(location="bangalore", budget=Budget.MEDIUM, cuisine="italian", min_rating=4.0)
    result = filter_service.apply(filter_df, prefs)
    assert isinstance(result, FilterResult)
    assert all(r.rating >= 4.0 for r in result.candidates)
    assert not any(r.name == "budget bites" for r in result.candidates)


def test_cap_limits_count(filter_service: FilterService) -> None:
    many = pd.DataFrame(
        [
            {
                "restaurant_id": f"r_{i}",
                "name": f"rest {i}",
                "city": "bangalore",
                "locality": "x",
                "cuisines_str": "italian",
                "rating": 3.0 + (i % 10) * 0.1,
                "cost_for_two": 400,
                "votes": i,
            }
            for i in range(30)
        ]
    )
    filter_service._settings.max_candidates_for_llm = 10
    prefs = UserPreferences(location="bangalore", budget=Budget.MEDIUM, min_rating=0.0)
    result = filter_service.apply(many, prefs)
    assert isinstance(result, FilterResult)
    assert len(result.candidates) == 10
    assert result.total_matched == 30


def test_no_match_empty(filter_service: FilterService, filter_df: pd.DataFrame) -> None:
    prefs = UserPreferences(
        location="bangalore",
        budget=Budget.MEDIUM,
        cuisine="italian",
        min_rating=5.0,
    )
    result = filter_service.apply(filter_df, prefs, available_cities=["bangalore", "new delhi"])
    assert isinstance(result, NoMatchResult)
    assert len(result.hints) >= 2


def test_invalid_preferences() -> None:
    with pytest.raises(ValidationError):
        UserPreferences(location="", budget=Budget.LOW)
    with pytest.raises(ValidationError):
        UserPreferences(location="bangalore", budget="cheap")  # type: ignore[arg-type]


def test_unknown_city_empty(filter_service: FilterService, filter_df: pd.DataFrame) -> None:
    prefs = UserPreferences(location="atlantis", budget=Budget.LOW, min_rating=0.0)
    result = filter_service.apply(filter_df, prefs)
    assert isinstance(result, NoMatchResult)


def test_whitespace_location_trimmed(filter_service: FilterService, filter_df: pd.DataFrame) -> None:
    prefs = UserPreferences(location="  bangalore  ", budget=Budget.MEDIUM, min_rating=0.0)
    result = filter_service.apply(filter_df, prefs)
    assert isinstance(result, FilterResult)
    assert result.total_matched > 0


def test_budget_boundary_inclusive(filter_service: FilterService) -> None:
    df = pd.DataFrame(
        [
            {
                "restaurant_id": "r_low_edge",
                "name": "edge low",
                "city": "bangalore",
                "locality": "x",
                "cuisines_str": "indian",
                "rating": 4.0,
                "cost_for_two": 300,
                "votes": 1,
            },
            {
                "restaurant_id": "r_med_edge",
                "name": "edge med",
                "city": "bangalore",
                "locality": "x",
                "cuisines_str": "indian",
                "rating": 4.0,
                "cost_for_two": 301,
                "votes": 1,
            },
        ]
    )
    low = filter_service.apply(df, UserPreferences(location="bangalore", budget=Budget.LOW, min_rating=0.0))
    med = filter_service.apply(df, UserPreferences(location="bangalore", budget=Budget.MEDIUM, min_rating=0.0))
    assert isinstance(low, FilterResult) and len(low.candidates) == 1
    assert isinstance(med, FilterResult) and len(med.candidates) == 1


def test_tie_breaking_by_votes(filter_service: FilterService) -> None:
    df = pd.DataFrame(
        [
            {
                "restaurant_id": "r_a",
                "name": "a",
                "city": "bangalore",
                "locality": "x",
                "cuisines_str": "italian",
                "rating": 4.5,
                "cost_for_two": 400,
                "votes": 10,
            },
            {
                "restaurant_id": "r_b",
                "name": "b",
                "city": "bangalore",
                "locality": "x",
                "cuisines_str": "italian",
                "rating": 4.5,
                "cost_for_two": 400,
                "votes": 100,
            },
        ]
    )
    capped = filter_service.cap_by_rating(df, 1)
    assert capped.iloc[0]["restaurant_id"] == "r_b"


def test_load_budget_tiers_from_config() -> None:
    from restaurant_rec.config.settings import find_project_root

    path = find_project_root() / "config" / "budget_tiers.yaml"
    tiers = load_budget_tiers(path)
    assert Budget.LOW in tiers
    assert tiers[Budget.MEDIUM][0] <= tiers[Budget.MEDIUM][1]


@pytest.mark.integration
def test_sample_query_on_real_cache() -> None:
    """Bangalore + medium + Italian + 4.0 on live cache (requires Phase 1 data)."""
    from restaurant_rec.config.settings import get_settings
    from restaurant_rec.infrastructure import RestaurantRepository

    settings = get_settings()
    if not settings.data_cache_path_resolved.exists():
        pytest.skip("Cache not built; run --refresh-data first")

    repo = RestaurantRepository.from_settings(settings)
    service = FilterService(settings=settings)
    prefs = UserPreferences(
        location="bangalore",
        budget=Budget.MEDIUM,
        cuisine="italian",
        min_rating=4.0,
    )
    result = service.apply(repo.dataframe, prefs, available_cities=repo.distinct_cities())
    assert isinstance(result, FilterResult)
    assert len(result.candidates) >= 1
