"""Deterministic filtering of restaurants by user preferences."""

from __future__ import annotations

import logging

import pandas as pd

from restaurant_rec.config.settings import Settings, get_settings
from restaurant_rec.domain.filter_results import FilterResult, NoMatchResult
from restaurant_rec.domain.models import Restaurant
from restaurant_rec.domain.preferences import UserPreferences, normalize_location
from restaurant_rec.infrastructure.restaurant_repository import row_to_restaurant
from restaurant_rec.domain.preferences import Budget
from restaurant_rec.services.budget_tiers import BudgetRange, cost_in_budget, load_budget_tiers

logger = logging.getLogger(__name__)


class FilterService:
    """Apply hard filters and cap candidates by rating."""

    def __init__(
        self,
        settings: Settings | None = None,
        budget_tiers: dict[Budget, BudgetRange] | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        if budget_tiers is None:
            budget_tiers = load_budget_tiers(self._settings.budget_tiers_path_resolved)
        self._budget_tiers = budget_tiers

    def apply(
        self,
        dataframe: pd.DataFrame,
        preferences: UserPreferences,
        *,
        available_cities: list[str] | None = None,
    ) -> FilterResult | NoMatchResult:
        """
        Filter restaurants and return top-N by rating.

        Pure function over the input DataFrame (no mutation, no I/O).
        """
        filtered = self._apply_filters(dataframe, preferences)
        total_matched = len(filtered)

        if total_matched == 0:
            return NoMatchResult(
                preferences=preferences,
                hints=self._build_hints(preferences, available_cities or []),
            )

        capped = self.cap_by_rating(filtered, self._settings.max_candidates_for_llm)
        candidates = [row_to_restaurant(row) for _, row in capped.iterrows()]

        logger.info(
            "Filter matched %s rows, returning %s candidates (cap=%s)",
            total_matched,
            len(candidates),
            self._settings.max_candidates_for_llm,
        )
        return FilterResult(
            candidates=candidates,
            total_matched=total_matched,
            preferences=preferences,
        )

    def _apply_filters(self, df: pd.DataFrame, preferences: UserPreferences) -> pd.DataFrame:
        work = df.copy()
        work = work[self._location_mask(work, preferences.location)]
        if preferences.cuisine:
            work = work[self._cuisine_mask(work, preferences.cuisine)]
        work = work[work["rating"] >= preferences.min_rating]
        work = work[
            work["cost_for_two"].apply(
                lambda cost: cost_in_budget(float(cost), preferences.budget, self._budget_tiers)
            )
        ]
        return work

    @staticmethod
    def _location_mask(df: pd.DataFrame, location: str) -> pd.Series:
        """Match city or locality (case-insensitive). Supports partial city names (e.g. delhi → new delhi)."""
        loc = normalize_location(location)
        city = df["city"].fillna("").str.lower()
        locality = df["locality"].fillna("").str.lower()

        city_exact = city == loc
        city_partial = city.str.contains(loc, regex=False)
        locality_exact = locality == loc
        locality_partial = locality.str.contains(loc, regex=False)
        return city_exact | city_partial | locality_exact | locality_partial

    @staticmethod
    def _cuisine_mask(df: pd.DataFrame, cuisine: str) -> pd.Series:
        needle = cuisine.strip().lower()
        cuisines = df["cuisines_str"].fillna("").str.lower()
        return cuisines.str.contains(needle, regex=False)

    @staticmethod
    def cap_by_rating(df: pd.DataFrame, max_count: int) -> pd.DataFrame:
        """Sort by rating desc, then votes desc, then name; return top max_count rows."""
        if len(df) <= max_count:
            return df.sort_values(
                ["rating", "votes", "name"],
                ascending=[False, False, True],
                na_position="last",
            )

        sorted_df = df.sort_values(
            ["rating", "votes", "name"],
            ascending=[False, False, True],
            na_position="last",
        )
        return sorted_df.head(max_count)

    @staticmethod
    def _build_hints(preferences: UserPreferences, available_cities: list[str]) -> list[str]:
        hints = [
            "No restaurants matched all filters.",
            "Try lowering --min-rating or choosing a different budget tier.",
        ]
        if preferences.cuisine:
            hints.append(f"Try a broader cuisine than '{preferences.cuisine}'.")
        if available_cities:
            preview = ", ".join(available_cities[:8])
            suffix = "..." if len(available_cities) > 8 else ""
            hints.append(f"Available cities in dataset: {preview}{suffix}")
        else:
            hints.append("Check spelling for city or locality name.")
        return hints
