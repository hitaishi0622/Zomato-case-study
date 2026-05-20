"""Tests for RestaurantRepository."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from restaurant_rec.domain.models import Restaurant
from restaurant_rec.infrastructure.cache_io import write_cache
from restaurant_rec.infrastructure.restaurant_repository import RestaurantRepository


@pytest.fixture
def repository(preprocessed_df: pd.DataFrame) -> RestaurantRepository:
    return RestaurantRepository(preprocessed_df)


def test_repository_get_all_returns_restaurant_models(repository: RestaurantRepository) -> None:
    restaurants = repository.get_all()
    assert len(restaurants) >= 2
    assert all(isinstance(r, Restaurant) for r in restaurants)
    first = restaurants[0]
    assert first.id
    assert first.name
    assert first.city
    assert first.cuisines
    assert first.rating >= 0
    assert first.cost_for_two >= 0


def test_get_by_ids_matching(repository: RestaurantRepository) -> None:
    all_ids = [r.id for r in repository.get_all()]
    found = repository.get_by_ids(all_ids[:1])
    assert len(found) == 1
    assert found[0].id == all_ids[0]


def test_get_by_ids_unknown_omitted(repository: RestaurantRepository) -> None:
    found = repository.get_by_ids(["r_nonexistent", "r_also_missing"])
    assert found == []


def test_repository_loads_cache(tmp_path: Path, preprocessed_df: pd.DataFrame) -> None:
    cache_path = tmp_path / "restaurants.parquet"
    write_cache(preprocessed_df, cache_path)

    from restaurant_rec.infrastructure.cache_io import read_cache

    loaded = read_cache(cache_path)
    repo = RestaurantRepository(loaded)
    assert repo.row_count > 0
    assert "restaurant_id" in repo.dataframe.columns
    assert "cost_for_two" in repo.dataframe.columns


def test_distinct_cities(repository: RestaurantRepository) -> None:
    cities = repository.distinct_cities()
    assert "bangalore" in cities
    assert "new delhi" in cities
