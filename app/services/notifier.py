"""atd-alert HTTP client: POST /v1/messages."""

from __future__ import annotations

import logging

import requests

from config.settings import NotifierSettings

LOGGER = logging.getLogger(__name__)

BODY_SNIPPET_CHARS = 200
MESSAGES_PATH = "/v1/messages"
API_KEY_HEADER = "X-API-Key"


def build_payload(text: str, topic: str) -> dict:
    """Build the atd-alert request body (raw HTML, no link preview)."""
    return {
        "topic": topic,
        "text": text,
        "format": "raw",
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }


def send_message(text: str, settings: NotifierSettings, token: str) -> None:
    """Deliver one message via atd-alert; non-2xx responses raise."""
    if not text.strip():
        raise ValueError("message text must not be empty")
    if not token.strip():
        raise ValueError("atd-alert token must not be empty")

    response = requests.post(
        f"{settings.url}{MESSAGES_PATH}",
        headers={API_KEY_HEADER: token},
        json=build_payload(text, settings.topic),
        timeout=settings.timeout_seconds,
    )
    if not 200 <= response.status_code < 300:
        snippet = response.text[:BODY_SNIPPET_CHARS]
        raise RuntimeError(
            f"atd-alert send failed: status={response.status_code} body={snippet}"
        )
    LOGGER.info("sent message via atd-alert: %s chars", len(text))
