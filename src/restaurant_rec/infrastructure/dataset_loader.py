"""Load raw Zomato data from Hugging Face."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download

logger = logging.getLogger(__name__)

# Hugging Face: ManikaSaini/zomato-restaurant-recommendation (file: zomato.csv)
HF_DATA_FILE = "zomato.csv"

# Source CSV column → internal name used before preprocessing
RAW_COLUMN_MAP: dict[str, str] = {
    "name": "name",
    "rate": "rate",
    "votes": "votes",
    "location": "location",
    "cuisines": "cuisines",
    "address": "address",
    "approx_cost(for two people)": "approx_cost",
    "listed_in(city)": "listed_in_city",
}


class DatasetLoadError(Exception):
    """Raised when the dataset cannot be loaded from Hugging Face."""


def download_dataset_csv(dataset_id: str, cache_dir: Path | None = None) -> Path:
    """
    Download zomato.csv from the Hugging Face dataset repository.

    Uses huggingface_hub instead of datasets.load_dataset for broader Python compatibility.
    """
    try:
        path = hf_hub_download(
            repo_id=dataset_id,
            filename=HF_DATA_FILE,
            repo_type="dataset",
            cache_dir=str(cache_dir) if cache_dir else None,
        )
        return Path(path)
    except Exception as exc:  # noqa: BLE001 — wrap HF/network errors
        raise DatasetLoadError(
            f"Failed to download dataset '{dataset_id}' ({HF_DATA_FILE}). "
            "Check network connectivity and dataset id."
        ) from exc


def load_raw_dataframe(dataset_id: str, cache_dir: Path | None = None) -> pd.DataFrame:
    """Download (if needed) and read the raw CSV into a DataFrame."""
    csv_path = download_dataset_csv(dataset_id, cache_dir=cache_dir)
    logger.info("Reading raw dataset from %s", csv_path)
    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:  # noqa: BLE001
        raise DatasetLoadError(f"Failed to read CSV at {csv_path}") from exc

    missing = [src for src in RAW_COLUMN_MAP if src not in df.columns]
    if missing:
        raise DatasetLoadError(
            f"Dataset schema mismatch. Missing columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    renamed = df[list(RAW_COLUMN_MAP.keys())].rename(columns=RAW_COLUMN_MAP)
    logger.info("Loaded %s raw rows from Hugging Face", len(renamed))
    return renamed
