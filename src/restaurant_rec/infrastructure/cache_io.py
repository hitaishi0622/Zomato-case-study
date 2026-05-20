"""Read and write cached restaurant DataFrames."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_CACHE_COLUMNS = frozenset(
    {
        "restaurant_id",
        "name",
        "city",
        "locality",
        "cuisines_str",
        "rating",
        "cost_for_two",
        "votes",
    }
)


class CacheError(Exception):
    """Raised when the local cache is missing or corrupt."""


def _validate_cache_df(df: pd.DataFrame) -> None:
    missing = REQUIRED_CACHE_COLUMNS - set(df.columns)
    if missing:
        raise CacheError(f"Cache is missing required columns: {sorted(missing)}")
    if len(df) == 0:
        raise CacheError("Cache file is empty.")


def write_cache(df: pd.DataFrame, path: Path) -> Path:
    """Persist DataFrame to Parquet (preferred) or CSV fallback."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".parquet":
        try:
            df.to_parquet(path, index=False)
            logger.info("Wrote cache to %s (%s rows)", path, len(df))
            return path
        except ImportError:
            path = path.with_suffix(".csv")
    df.to_csv(path, index=False)
    logger.info("Wrote cache to %s (%s rows)", path, len(df))
    return path


def read_cache(path: Path) -> pd.DataFrame:
    """Load cached data from Parquet or CSV."""
    if not path.is_file():
        csv_alt = path.with_suffix(".csv") if path.suffix == ".parquet" else None
        if csv_alt and csv_alt.is_file():
            path = csv_alt
        else:
            raise CacheError(f"Cache not found at {path}. Run with --refresh-data to build.")

    try:
        if path.suffix.lower() == ".parquet":
            df = pd.read_parquet(path)
        else:
            df = pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001
        raise CacheError(
            f"Failed to read cache at {path}. File may be corrupt; use --refresh-data."
        ) from exc

    _validate_cache_df(df)
    logger.info("Loaded cache from %s (%s rows)", path, len(df))
    return df


def resolve_cache_path(configured_path: Path) -> Path:
    """Return existing cache path (parquet or csv sibling)."""
    if configured_path.is_file():
        return configured_path
    if configured_path.suffix == ".parquet":
        csv_path = configured_path.with_suffix(".csv")
        if csv_path.is_file():
            return csv_path
    return configured_path
