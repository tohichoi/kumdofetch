"""Typed configuration loader: tomllib + pydantic (os-environment.md SSOT).

Every application setting is read through these models. Missing keys or type
mismatches fail fast with the offending field path (code-quality.md §7).
The atd-alert caller token is read from the environment only, never from TOML.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, model_validator

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = BASE_DIR / "config" / "config.toml"

ENV_CONFIG_PATH = "ATD_CONFIG"
ENV_ALERT_TOKEN = "ATD_ALERT_TOKEN"


class NotifierSettings(BaseModel):
    url: str = Field(pattern=r"^https?://")
    topic: str = Field(min_length=1)
    timeout_seconds: float = Field(gt=0)
    message_max_chars: int = Field(gt=0)
    test_message: str = Field(min_length=1)
    empty_message: str = Field(min_length=1)


class ScraperSettings(BaseModel):
    timeout_seconds: float = Field(gt=0)


class SchedulerSettings(BaseModel):
    interval_seconds: int = Field(gt=0)
    max_consecutive_failures: int = Field(gt=0)


class StateSettings(BaseModel):
    path: str = Field(min_length=1)

    @property
    def resolved_path(self) -> Path:
        path = Path(self.path)
        return path if path.is_absolute() else (BASE_DIR / path)


class SourceSettings(BaseModel):
    name: str = Field(min_length=1)
    url: str = Field(pattern=r"^https?://")
    table_index: int = Field(ge=0)
    title_prefix: str


class Settings(BaseModel):
    notifier: NotifierSettings
    scraper: ScraperSettings
    scheduler: SchedulerSettings
    state: StateSettings
    sources: list[SourceSettings] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_source_names(self) -> Settings:
        names = [source.name for source in self.sources]
        if len(names) != len(set(names)):
            raise ValueError("source names must be unique")
        return self


def _read_toml(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"invalid TOML in {path}: {exc}") from exc


def load_settings(path: Path | None = None) -> Settings:
    """Load and validate settings; never silently substitutes defaults."""
    config_path = path or Path(os.environ.get(ENV_CONFIG_PATH, DEFAULT_CONFIG_PATH))
    raw = _read_toml(config_path)
    try:
        return Settings.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"invalid settings in {config_path}: {exc}") from exc


def load_alert_token() -> str:
    """Return the atd-alert caller token or fail fast; never log the value."""
    token = os.environ.get(ENV_ALERT_TOKEN, "").strip()
    if not token:
        raise RuntimeError(f"{ENV_ALERT_TOKEN} environment variable is required")
    return token
