"""Collection loop failure threshold and counter reset."""

from __future__ import annotations

import pytest

from app.controllers import cli
from config.settings import (
    NotifierSettings,
    SchedulerSettings,
    ScraperSettings,
    Settings,
    SourceSettings,
    StateSettings,
)


def _settings(max_consecutive_failures: int) -> Settings:
    return Settings(
        notifier=NotifierSettings(
            url="http://atd-alert:8099",
            topic="대한검도회",
            timeout_seconds=1,
            message_max_chars=4096,
            test_message="test",
            empty_message="empty",
        ),
        scraper=ScraperSettings(timeout_seconds=1),
        scheduler=SchedulerSettings(
            interval_seconds=1,
            max_consecutive_failures=max_consecutive_failures,
        ),
        state=StateSettings(path="state.pickle"),
        sources=[
            SourceSettings(
                name="board",
                url="http://example.com/notice",
                table_index=0,
                title_prefix="[test]",
            )
        ],
    )


def _install_cycle(monkeypatch: pytest.MonkeyPatch, outcomes: list[bool]) -> list[int]:
    calls: list[int] = []

    def fake_run_cycle(*args) -> None:
        calls.append(len(calls))
        if outcomes[len(calls) - 1]:
            raise RuntimeError("boom")

    monkeypatch.setattr(cli, "run_cycle", fake_run_cycle)
    monkeypatch.setattr(cli.time, "sleep", lambda seconds: None)
    return calls


def test_run_forever_raises_at_failure_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _install_cycle(monkeypatch, [True, True, True])

    with pytest.raises(RuntimeError, match="boom"):
        cli._run_forever(_settings(3), "test-token", False)

    assert len(calls) == 3


def test_run_forever_resets_counter_after_success(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _install_cycle(monkeypatch, [True, False, True, False, True, True])

    with pytest.raises(RuntimeError, match="boom"):
        cli._run_forever(_settings(2), "test-token", False)

    assert len(calls) == 6
