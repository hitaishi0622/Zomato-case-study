"""Tests for data preprocessing."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from restaurant_rec.infrastructure.preprocessor import preprocess_dataframe, update_budget_tiers_yaml


@pytest.fixture
def raw_sample_df() -> pd.DataFrame:
    path = Path(__file__).parent / "fixtures" / "raw_sample.csv"
    return pd.read_csv(path)


def test_preprocessor_assigns_unique_ids(raw_sample_df: pd.DataFrame) -> None:
    result = preprocess_dataframe(raw_sample_df)
    assert len(result) >= 2
    assert result["restaurant_id"].is_unique
    assert result["restaurant_id"].str.startswith("r_").all()


def test_no_null_ratings_after_clean(raw_sample_df: pd.DataFrame) -> None:
    result = preprocess_dataframe(raw_sample_df)
    assert result["rating"].notna().all()
    assert (result["rating"] >= 0).all()
    assert (result["rating"] <= 5).all()
    # NEW rating row and bad cost row should be dropped
    names = set(result["name"].tolist())
    assert "jalsa" in names
    assert "no rating place" not in names
    assert "bad cost cafe" not in names


def test_city_and_cuisine_normalized(raw_sample_df: pd.DataFrame) -> None:
    result = preprocess_dataframe(raw_sample_df)
    assert all(city == city.lower() for city in result["city"])
    delhi_rows = result[result["city"] == "new delhi"]
    assert len(delhi_rows) == 1
    assert delhi_rows.iloc[0]["name"] == "delhi diner"


def test_update_budget_tiers_yaml(tmp_path: Path, raw_sample_df: pd.DataFrame) -> None:
    clean = preprocess_dataframe(raw_sample_df)
    out = tmp_path / "budget_tiers.yaml"
    tiers = update_budget_tiers_yaml(clean, out)
    assert out.is_file()
    assert "low" in tiers and "medium" in tiers and "high" in tiers
