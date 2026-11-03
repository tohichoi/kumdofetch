"""Article data model shared by scraper, state and message rendering."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

WR_ID_PARAMS = ("wr_id", "idx")
BOARD_PARAM = "board"


def article_key(href: str, fallback: str) -> str:
    """Stable key: host + board + post id when present, else the caller's fallback."""
    parsed = urlparse(href)
    query = parse_qs(parsed.query)
    board = query.get(BOARD_PARAM, [""])[0]
    for param in WR_ID_PARAMS:
        post_id = query.get(param, [""])[0]
        if post_id.isdigit():
            parts = [parsed.netloc] + ([board] if board else []) + [post_id]
            return "#".join(parts)
    return fallback


@dataclass(frozen=True, slots=True)
class Article:
    key: str
    title: str
    href: str
    title_prefix: str
    date: str = ""
