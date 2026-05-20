"""Application settings: YAML defaults with environment variable overrides."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

LLMProvider = Literal["groq", "openai", "anthropic", "ollama"]

_SETTINGS_FILENAME = "settings.yaml"
_CONFIG_DIRNAME = "config"


def find_project_root(start: Path | None = None) -> Path:
    """Walk parents until pyproject.toml is found; fall back to cwd."""
    current = (start or Path(__file__)).resolve()
    for path in (current, *current.parents):
        if (path / "pyproject.toml").is_file():
            return path
    return Path.cwd()


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else {}


class Settings(BaseSettings):
    """Settings loaded from config/settings.yaml, overridden by environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    hf_dataset_id: str = Field(
        default="ManikaSaini/zomato-restaurant-recommendation",
        description="Hugging Face dataset identifier",
    )
    data_cache_path: str = Field(
        default="data/restaurants.parquet",
        description="Local path for cached restaurant data",
    )
    max_candidates_for_llm: int = Field(
        default=15,
        ge=1,
        le=50,
        description="Maximum candidates sent to the LLM",
    )
    max_recommendations: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum recommendations shown to the user",
    )
    llm_provider: LLMProvider = Field(default="groq")
    llm_model: str = Field(default="llama-3.3-70b-versatile")
    llm_api_key: str | None = Field(
        default=None,
        description="Set via GROQ_API_KEY or LLM_API_KEY env var",
    )
    llm_temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    llm_timeout_sec: int = Field(default=60, ge=1, le=300)
    budget_tiers_path: str = Field(default="config/budget_tiers.yaml")

    @field_validator("llm_provider", mode="before")
    @classmethod
    def normalize_provider(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @property
    def data_cache_path_resolved(self) -> Path:
        path = Path(self.data_cache_path)
        if path.is_absolute():
            return path
        return find_project_root() / path

    @property
    def budget_tiers_path_resolved(self) -> Path:
        path = Path(self.budget_tiers_path)
        if path.is_absolute():
            return path
        return find_project_root() / path

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Priority (high to low): init kwargs → env → .env → YAML → defaults."""

        def yaml_source() -> dict[str, Any]:
            root = find_project_root()
            path = root / _CONFIG_DIRNAME / _SETTINGS_FILENAME
            return _load_yaml(path)

        return (
            init_settings,
            env_settings,
            dotenv_settings,
            yaml_source,
            file_secret_settings,
        )

    @classmethod
    def from_yaml(
        cls,
        yaml_path: Path | None = None,
        project_root: Path | None = None,
    ) -> Settings:
        """Load settings using YAML + environment (env wins over YAML)."""
        if yaml_path is not None:
            return cls(**_load_yaml(yaml_path))
        if project_root is not None:
            path = project_root / _CONFIG_DIRNAME / _SETTINGS_FILENAME
            return cls(**_load_yaml(path))
        return cls()


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    env_path = find_project_root() / ".env"
    if env_path.is_file():
        load_dotenv(env_path, override=False)
    return Settings.from_yaml()


def clear_settings_cache() -> None:
    """Clear cached settings (useful in tests)."""
    get_settings.cache_clear()
