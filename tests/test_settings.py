"""Tests for application settings (Phase 0)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from restaurant_rec.config.settings import Settings, find_project_root, get_settings


def test_find_project_root_locates_pyproject() -> None:
    root = find_project_root()
    assert (root / "pyproject.toml").is_file()


def test_settings_load_defaults_from_yaml() -> None:
    root = find_project_root()
    settings = Settings.from_yaml(project_root=root)
    assert settings.hf_dataset_id == "ManikaSaini/zomato-restaurant-recommendation"
    assert settings.data_cache_path == "data/restaurants.parquet"
    assert settings.max_candidates_for_llm == 15
    assert settings.max_recommendations == 5
    assert settings.llm_provider == "groq"
    assert settings.llm_model == "llama-3.3-70b-versatile"
    assert settings.llm_temperature == 0.2


def test_get_settings_cached() -> None:
    a = get_settings()
    b = get_settings()
    assert a is b


def test_environment_overrides_yaml(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_CACHE_PATH", "data/custom.parquet")
    monkeypatch.setenv("MAX_CANDIDATES_FOR_LLM", "10")
    settings = Settings.from_yaml()
    assert settings.data_cache_path == "data/custom.parquet"
    assert settings.max_candidates_for_llm == 10


def test_invalid_max_candidates_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(max_candidates_for_llm=0)
    with pytest.raises(ValidationError):
        Settings(max_candidates_for_llm=-1)


def test_invalid_llm_provider_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(llm_provider="invalid")  # type: ignore[arg-type]


def test_resolved_paths_are_under_project_root() -> None:
    settings = Settings.from_yaml()
    root = find_project_root()
    assert settings.data_cache_path_resolved == root / "data" / "restaurants.parquet"
    assert settings.budget_tiers_path_resolved == root / "config" / "budget_tiers.yaml"


def test_budget_tiers_file_exists() -> None:
    settings = Settings.from_yaml()
    assert settings.budget_tiers_path_resolved.is_file()


def test_llm_api_key_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test-secret-key")
    settings = Settings.from_yaml()
    assert settings.llm_api_key == "test-secret-key"
    monkeypatch.delenv("LLM_API_KEY", raising=False)
