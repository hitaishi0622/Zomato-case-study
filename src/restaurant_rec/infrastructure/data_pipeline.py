"""Orchestrate download, preprocess, cache, and budget tier updates."""

from __future__ import annotations

import logging
import time

import pandas as pd

from restaurant_rec.config.settings import Settings
from restaurant_rec.infrastructure.cache_io import CacheError, read_cache, write_cache
from restaurant_rec.infrastructure.dataset_loader import DatasetLoadError, load_raw_dataframe
from restaurant_rec.infrastructure.preprocessor import preprocess_dataframe, update_budget_tiers_yaml

logger = logging.getLogger(__name__)


def log_dataset_stats(df: pd.DataFrame) -> None:
    """Log summary statistics after load or ingest."""
    cities = df["city"].nunique()
    top_cities = df["city"].value_counts().head(5).to_dict()
    logger.info(
        "Dataset stats: rows=%s, distinct_cities=%s, top_cities=%s, "
        "rating_mean=%.2f, cost_median=%.0f",
        len(df),
        cities,
        top_cities,
        df["rating"].mean(),
        df["cost_for_two"].median(),
    )


def ingest_and_cache(settings: Settings) -> pd.DataFrame:
    """Download from Hugging Face, preprocess, write cache, update budget tiers."""
    logger.info("Starting dataset ingest for %s", settings.hf_dataset_id)
    raw_df = load_raw_dataframe(settings.hf_dataset_id)
    clean_df = preprocess_dataframe(raw_df)
    if clean_df.empty:
        raise DatasetLoadError("Preprocessing produced zero rows.")

    cache_path = write_cache(clean_df, settings.data_cache_path_resolved)
    settings.data_cache_path_resolved  # ensure parent exists
    update_budget_tiers_yaml(clean_df, settings.budget_tiers_path_resolved)
    log_dataset_stats(clean_df)
    logger.info("Ingest complete; cache at %s", cache_path)
    return clean_df


def load_restaurant_dataframe(settings: Settings, *, refresh: bool = False) -> pd.DataFrame:
    """
    Load restaurants from cache, or ingest when refresh=True or cache is missing.

    On corrupt cache, raises CacheError (caller may retry with refresh).
    """
    cache_path = settings.data_cache_path_resolved

    if refresh:
        return ingest_and_cache(settings)

    try:
        from restaurant_rec.infrastructure.cache_io import resolve_cache_path

        resolved = resolve_cache_path(cache_path)
        if resolved.is_file():
            start = time.perf_counter()
            df = read_cache(resolved)
            elapsed = time.perf_counter() - start
            logger.info("Cache load completed in %.2fs", elapsed)
            log_dataset_stats(df)
            return df
    except CacheError:
        logger.warning("Cache unavailable or invalid; triggering ingest.")

    return ingest_and_cache(settings)
