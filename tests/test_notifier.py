"""atd-alert payload shape and HTTP error handling."""

from __future__ import annotations

import pytest

from app.services import notifier
from config.settings import NotifierSettings


def _settings() -> NotifierSettings:
    return NotifierSettings(
        url="http://atd-alert:8099",
        topic="대한검도회",
        timeout_seconds=5,
        message_max_chars=4096,
        test_message="test",
        empty_message="empty",
    )


class _Response:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


def test_build_payload_shape() -> None:
    payload = notifier.build_payload("<b>hello</b>", "대한검도회")

    assert payload == {
        "topic": "대한검도회",
        "text": "<b>hello</b>",
        "format": "raw",
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }


def test_send_message_posts_to_atd_alert(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def fake_post(url: str, **kwargs) -> _Response:
        captured["url"] = url
        captured.update(kwargs)
        return _Response(200)

    monkeypatch.setattr(notifier.requests, "post", fake_post)

    notifier.send_message("hello", _settings(), "test-token")

    assert captured["url"] == "http://atd-alert:8099/v1/messages"
    assert captured["headers"] == {"X-API-Key": "test-token"}
    assert captured["timeout"] == 5
    assert captured["json"]["topic"] == "대한검도회"
    assert captured["json"]["format"] == "raw"
    assert captured["json"]["parse_mode"] == "HTML"
    assert captured["json"]["disable_web_page_preview"] is True


def test_send_message_raises_on_non_2xx(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        notifier.requests, "post", lambda *args, **kwargs: _Response(401, "unauthorized")
    )

    with pytest.raises(RuntimeError, match="status=401"):
        notifier.send_message("hello", _settings(), "test-token")


def test_send_message_rejects_empty_text() -> None:
    with pytest.raises(ValueError, match="empty"):
        notifier.send_message("   ", _settings(), "test-token")
