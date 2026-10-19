"""CLI entry logic: argument parsing and the collection loop."""

from __future__ import annotations

import argparse
import logging
import time

from app.models.article import Article
from app.services.notifier import send_message
from app.services.scraper import collect_new_articles
from app.services.state import ArticleState, load_state, save_state
from app.views.message import render_messages
from config.settings import Settings, load_alert_token, load_settings

LOGGER = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="kumdofetch",
        description="Collect kumdo board notices and send them via atd-alert.",
    )
    parser.add_argument("--once", action="store_true", help="run one collection cycle and exit")
    parser.add_argument("--test", action="store_true", help="send one test message and exit")
    parser.add_argument(
        "--notify-empty",
        action="store_true",
        help="send a message when no new articles are found",
    )
    return parser.parse_args(argv)


def run_cycle(settings: Settings, token: str, notify_empty: bool) -> None:
    """Collect, send and persist one cycle."""
    state = load_state(settings.state.resolved_path)
    new_articles = collect_new_articles(
        settings.sources, set(state), settings.scraper.timeout_seconds
    )
    messages = render_messages(new_articles.values(), settings.notifier.message_max_chars)

    if messages:
        for message in messages:
            send_message(message, settings.notifier, token)
    elif notify_empty:
        send_message(settings.notifier.empty_message, settings.notifier, token)

    if new_articles:
        state.update(_to_state(new_articles))
        save_state(settings.state.resolved_path, state)
    LOGGER.info("cycle complete: %s new article(s)", len(new_articles))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    settings = load_settings()
    token = load_alert_token()

    if args.test:
        send_message(settings.notifier.test_message, settings.notifier, token)
        return 0

    if args.once:
        run_cycle(settings, token, args.notify_empty)
        return 0

    _run_forever(settings, token, args.notify_empty)
    return 0


def _run_forever(settings: Settings, token: str, notify_empty: bool) -> None:
    failures = 0
    while True:
        try:
            run_cycle(settings, token, notify_empty)
        except Exception:
            failures += 1
            LOGGER.exception(
                "collection cycle failed (%s/%s)",
                failures,
                settings.scheduler.max_consecutive_failures,
            )
            if failures >= settings.scheduler.max_consecutive_failures:
                raise
        else:
            failures = 0
        time.sleep(settings.scheduler.interval_seconds)


def _to_state(articles: dict[str, Article]) -> ArticleState:
    return {key: (article.title, article.href) for key, article in articles.items()}
