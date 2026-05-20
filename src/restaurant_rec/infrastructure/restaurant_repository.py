"""In-memory restaurant store backed by cached DataFrame."""

from __future__ import annotations

import logging
from typing import Iterable

import pandas as pd

from restaurant_rec.config.settings import Settings
from restaurant_rec.domain.models import Restaurant
from restaurant_rec.infrastructure.data_pipeline import load_restaurant_dataframe

logger = logging.getLogger(__name__)


def row_to_restaurant(row: pd.Series) -> Restaurant:
    cuisines_raw = row.get("cuisines_str") or ""
    cuisines = [c.strip() for c in str(cuisines_raw).split(",") if c.strip()]
    votes_val = row.get("votes")
    votes: int | None = None
    if votes_val is not None and not pd.isna(votes_val):
        votes = int(votes_val)

    locality = row.get("locality")
    if locality is not None and pd.isna(locality):
        locality = None

    return Restaurant(
        id=str(row["restaurant_id"]),
        name=str(row["name"]),
        city=str(row["city"]),
        locality=str(locality) if locality else None,
        cuisines=cuisines,
        rating=float(row["rating"]),
        cost_for_two=float(row["cost_for_two"]),
        votes=votes,
    )


class RestaurantRepository:
    """Queryable store of preprocessed restaurants."""

    def __init__(self, dataframe: pd.DataFrame) -> None:
        self._df = dataframe.set_index("restaurant_id", drop=False)

    @classmethod
    def from_settings(cls, settings: Settings | None = None, *, refresh: bool = False) -> RestaurantRepository:
        settings = settings or Settings()
        df = load_restaurant_dataframe(settings, refresh=refresh)
        return cls(df)

    @property
    def dataframe(self) -> pd.DataFrame:
        return self._df.copy()

    @property
    def row_count(self) -> int:
        return len(self._df)

    def get_all(self) -> list[Restaurant]:
        return [row_to_restaurant(row) for _, row in self._df.iterrows()]

    def get_by_ids(self, restaurant_ids: Iterable[str]) -> list[Restaurant]:
        """Return restaurants for known ids; unknown ids are omitted."""
        results: list[Restaurant] = []
        for rid in restaurant_ids:
            if rid in self._df.index:
                results.append(row_to_restaurant(self._df.loc[rid]))
        return results

    def distinct_cities(self) -> list[str]:
        return sorted(self._df["city"].unique().tolist())
