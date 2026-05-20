"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from restaurant_rec.config.settings import clear_settings_cache
from restaurant_rec.infrastructure.preprocessor import preprocess_dataframe


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "slow: tests that download from Hugging Face")


@pytest.fixture
def preprocessed_df() -> pd.DataFrame:
    raw_path = Path(__file__).parent / "fixtures" / "raw_sample.csv"
    return preprocess_dataframe(pd.read_csv(raw_path))


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    """Ensure settings cache does not leak between tests."""
    clear_settings_cache()
    yield
    clear_settings_cache()
