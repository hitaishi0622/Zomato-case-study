"""Clean and normalize raw restaurant data."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

import pandas as pd
import yaml

logger = logging.getLogger(__name__)

# Metro cities recognized in address text (extend as needed)
_METRO_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bbengaluru\b", re.I), "bangalore"),
    (re.compile(r"\bbangalore\b", re.I), "bangalore"),
    (re.compile(r"\bnew delhi\b", re.I), "new delhi"),
    (re.compile(r"\bdelhi\b", re.I), "delhi"),
    (re.compile(r"\bmumbai\b", re.I), "mumbai"),
    (re.compile(r"\bhyderabad\b", re.I), "hyderabad"),
    (re.compile(r"\bchennai\b", re.I), "chennai"),
    (re.compile(r"\bkolkata\b", re.I), "kolkata"),
    (re.compile(r"\bpune\b", re.I), "pune"),
    (re.compile(r"\bgurgaon\b", re.I), "gurgaon"),
    (re.compile(r"\bnoida\b", re.I), "noida"),
]

_RATE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)")


def _normalize_text(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip().lower()
    return text or None


def _parse_rating(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text or text in {"-", "new", "nan"}:
        return None
    if text.lower() == "new":
        return None
    match = _RATE_PATTERN.search(text.replace(" ", ""))
    if not match:
        return None
    rating = float(match.group(1))
    if rating > 5.0:
        rating = rating / 10.0 if rating <= 50 else None
    if rating is None or rating < 0 or rating > 5:
        return None
    return round(rating, 2)


def _parse_cost(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)) and not pd.isna(value):
        cost = float(value)
        return cost if cost >= 0 else None
    text = str(value).strip().lower()
    if not text or text in {"-", "nan"}:
        return None
    digits = re.sub(r"[^\d.]", "", text.split("-")[0])
    if not digits:
        return None
    try:
        cost = float(digits)
    except ValueError:
        return None
    return cost if cost >= 0 else None


def _extract_city_from_address(address: Any) -> str | None:
    if address is None or (isinstance(address, float) and pd.isna(address)):
        return None
    text = str(address)
    for pattern, city in _METRO_PATTERNS:
        if pattern.search(text):
            return city
    return None


def _parse_cuisines(value: Any) -> list[str]:
    text = _normalize_text(value)
    if not text:
        return []
    parts = re.split(r"\s*,\s*", text)
    return [part.strip() for part in parts if part.strip()]


def _make_restaurant_id(name: str, city: str, locality: str | None) -> str:
    key = f"{name}|{city}|{locality or ''}"
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()[:12]
    return f"r_{digest}"


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform raw mapped columns into the canonical cache schema.

    Rows without a valid name, city, rating, or cost are dropped.
    """
    work = df.copy()
    initial_count = len(work)

    work["name"] = work["name"].apply(lambda v: _normalize_text(v))
    work["city"] = work["address"].apply(_extract_city_from_address)
    work["locality"] = work["location"].apply(_normalize_text)
    work["rating"] = work["rate"].apply(_parse_rating)
    work["cost_for_two"] = work["approx_cost"].apply(_parse_cost)
    work["cuisines"] = work["cuisines"].apply(_parse_cuisines)
    work["votes"] = pd.to_numeric(work["votes"], errors="coerce").astype("Int64")

    work = work.dropna(subset=["name", "city", "rating", "cost_for_two"])
    work["city"] = work["city"].astype(str)
    work["name"] = work["name"].astype(str)
    work["locality"] = work["locality"].where(work["locality"].notna(), None)

    work["restaurant_id"] = work.apply(
        lambda row: _make_restaurant_id(row["name"], row["city"], row["locality"]),
        axis=1,
    )

    # Deduplicate by id (keep highest votes, then rating)
    work = work.sort_values(["votes", "rating"], ascending=False, na_position="last")
    work = work.drop_duplicates(subset=["restaurant_id"], keep="first")

    # Store cuisines as comma-separated for parquet/CSV simplicity
    work["cuisines_str"] = work["cuisines"].apply(lambda c: ", ".join(c))

    result = work[
        [
            "restaurant_id",
            "name",
            "city",
            "locality",
            "cuisines_str",
            "rating",
            "cost_for_two",
            "votes",
        ]
    ].reset_index(drop=True)

    dropped = initial_count - len(result)
    logger.info(
        "Preprocessed %s rows (%s dropped: missing name/city/rating/cost or duplicate ids)",
        len(result),
        dropped,
    )
    return result


def update_budget_tiers_yaml(df: pd.DataFrame, output_path: Path) -> dict[str, list[int]]:
    """
    Compute global budget tier thresholds from cost_for_two percentiles.

    Uses 33rd and 66th percentiles for low/medium/high boundaries.
    """
    costs = df["cost_for_two"].dropna()
    if costs.empty:
        tiers = {"low": [0, 500], "medium": [501, 1500], "high": [1501, 999999]}
    else:
        p33 = int(costs.quantile(0.33))
        p66 = int(costs.quantile(0.66))
        tiers = {
            "low": [0, p33],
            "medium": [p33 + 1, p66],
            "high": [p66 + 1, 999999],
        }

    payload = {"global": tiers}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, default_flow_style=False, sort_keys=False)
    logger.info("Updated budget tiers at %s: %s", output_path, tiers)
    return tiers
