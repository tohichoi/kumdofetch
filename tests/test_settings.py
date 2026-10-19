"""Settings loading and Fail-Fast behaviour."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.settings import Settings, load_alert_token, load_settings

VALID_CONFIG = """
[notifier]
url = "http://atd-alert:8099"
topic = "대한검도회"
timeout_seconds = 30
message_max_chars = 4096
test_message = "test"
empty_message = "empty"

[scraper]
timeout_seconds = 30

[scheduler]
interval_seconds = 7200
max_consecutive_failures = 3

[state]
path = "state.pickle"

[[sources]]
name = "board"
url = "http://example.com/notice"
table_index = 0
title_prefix = "[test]"
"""


def _write_config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_loads_valid_config(tmp_path: Path) -> None:
    settings = load_settings(_write_config(tmp_path, VALID_CONFIG))

    assert isinstance(settings, Settings)
    assert settings.sources[0].name == "board"
    assert settings.state.resolved_path.is_absolute()


def test_missing_field_fails_with_field_path(tmp_path: Path) -> None:
    broken = VALID_CONFIG.replace("[scheduler]\ninterval_seconds = 7200\n", "")

    with pytest.raises(ValueError, match="scheduler"):
        load_settings(_write_config(tmp_path, broken))


def test_missing_config_file_fails(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="config file not found"):
        load_settings(tmp_path / "missing.toml")


def test_missing_token_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ATD_ALERT_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="ATD_ALERT_TOKEN"):
        load_alert_token()


def test_token_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATD_ALERT_TOKEN", "dummy-token")

    assert load_alert_token() == "dummy-token"
