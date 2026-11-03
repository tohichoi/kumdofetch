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
    parser.add_argument(
        "--seed",
        action="store_true",
        help="record current board contents as known and exit without sending",
    )
    return parser.parse_args(argv)


def run_cycle(settings: Settings, token: str, notify_empty: bool) -> None:
    """Collect, send and persist one cycle."""
    state = load_state(settings.state.resolved_path)
    new_articles = _collect(settings, state)
    messages = render_messages(new_articles.values(), settings.notifier.message_max_chars)

    if messages:
        for message in messages:
            send_message(message, settings.notifier, token)
    elif notify_empty:
        send_message(settings.notifier.empty_message, settings.notifier, token)

    _remember(settings, state, new_articles)
    LOGGER.info("cycle complete: %s new article(s)", len(new_articles))


def seed_state(settings: Settings) -> int:
    """Record current board contents as known without sending anything."""
    state = load_state(settings.state.resolved_path)
    new_articles = _collect(settings, state)
    _remember(settings, state, new_articles)
    return len(new_articles)


def _collect(settings: Settings, state: ArticleState) -> dict[str, Article]:
    return collect_new_articles(
        settings.sources,
        set(state),
        settings.scraper.timeout_seconds,
        settings.scraper.max_pages,
    )


def _remember(settings: Settings, state: ArticleState, articles: dict[str, Article]) -> None:
    if articles:
        state.update(_to_state(articles))
        save_state(settings.state.resolved_path, state)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    settings = load_settings()

    if args.seed:
        LOGGER.info("seeded %s article(s) without notifying", seed_state(settings))
        return 0

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
