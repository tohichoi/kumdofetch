"""HTML message rendering and max-length chunking."""

from __future__ import annotations

import html
import logging
from collections.abc import Iterable
from urllib.parse import urlparse

from app.models.article import Article

LOGGER = logging.getLogger(__name__)

ELLIPSIS = "…"
ALLOWED_SCHEMES = frozenset({"http", "https"})


def render_line(article: Article, max_chars: int) -> str:
    """Render one article as an HTML link line, truncating an oversized title."""
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")

    href = html.escape(_validate_href(article.href, article.key), quote=True)
    template = f'{article.title_prefix} <a href="{href}">{{title}}</a>\n'
    budget = max_chars - len(template.format(title="")) - len(ELLIPSIS)
    if budget < 0:
        LOGGER.error("skipping %s: fixed markup exceeds %s chars", article.key, max_chars)
        return ""

    escaped_title = html.escape(article.title, quote=False)
    if len(escaped_title) > budget:
        LOGGER.warning(
            "truncating title for %s: %s > %s chars", article.key, len(escaped_title), budget
        )
        escaped_title = _truncate_escaped(article.title, budget)
    return template.format(title=escaped_title)


def render_messages(articles: Iterable[Article], max_chars: int) -> list[str]:
    """Group article lines into messages no longer than max_chars."""
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")

    messages: list[str] = []
    current = ""
    for article in articles:
        line = render_line(article, max_chars)
        if not line:
            continue
        if current and len(current) + len(line) > max_chars:
            messages.append(current)
            current = line
        else:
            current += line
    if current:
        messages.append(current)
    return messages


def _validate_href(href: str, key: str) -> str:
    value = href.strip()
    if not value:
        raise ValueError(f"empty href for {key}")
    scheme = urlparse(value).scheme.lower()
    if scheme and scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"refusing unsafe href for {key}: {href}")
    return value


def _truncate_escaped(title: str, budget: int) -> str:
    """Truncate raw title by escaped length and append the ellipsis."""
    parts: list[str] = []
    used = 0
    for char in title:
        piece = html.escape(char, quote=False)
        if used + len(piece) > budget:
            break
        parts.append(piece)
        used += len(piece)
    return "".join(parts) + ELLIPSIS
