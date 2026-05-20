"""Integration tests for data pipeline (network optional)."""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

from restaurant_rec.config.settings import Settings
from restaurant_rec.infrastructure.cache_io import CacheError, read_cache
from restaurant_rec.infrastructure.data_pipeline import load_restaurant_dataframe


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        data_cache_path=str(tmp_path / "restaurants.parquet"),
        budget_tiers_path=str(tmp_path / "budget_tiers.yaml"),
    )


def test_load_uses_cache_when_present(settings: Settings, preprocessed_df: pd.DataFrame) -> None:
    from restaurant_rec.infrastructure.cache_io import write_cache

    write_cache(preprocessed_df, settings.data_cache_path_resolved)
    with patch("restaurant_rec.infrastructure.data_pipeline.ingest_and_cache") as mock_ingest:
        df = load_restaurant_dataframe(settings, refresh=False)
        mock_ingest.assert_not_called()
    assert len(df) == len(preprocessed_df)


def test_refresh_triggers_ingest(settings: Settings, preprocessed_df: pd.DataFrame) -> None:
    with patch(
        "restaurant_rec.infrastructure.data_pipeline.ingest_and_cache",
        return_value=preprocessed_df,
    ) as mock_ingest:
        df = load_restaurant_dataframe(settings, refresh=True)
        mock_ingest.assert_called_once()
    assert len(df) == len(preprocessed_df)


def test_corrupt_cache_raises_cache_error(settings: Settings) -> None:
    path = settings.data_cache_path_resolved
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not valid parquet", encoding="utf-8")
    with pytest.raises(CacheError):
        read_cache(path)


@pytest.mark.slow
def test_hf_ingest_builds_cache(settings: Settings) -> None:
    """Downloads from Hugging Face; run with: pytest -m slow."""
    df = load_restaurant_dataframe(settings, refresh=True)
    assert len(df) > 1000
    assert settings.data_cache_path_resolved.exists() or settings.data_cache_path_resolved.with_suffix(
        ".csv"
    ).exists()
