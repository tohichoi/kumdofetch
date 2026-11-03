"""Article data model shared by scraper, state and message rendering."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

WR_ID_PARAM = "wr_id"


def article_key(href: str, fallback: str) -> str:
    """Stable key: board host + wr_id when present, else the caller's fallback."""
    parsed = urlparse(href)
    wr_id = parse_qs(parsed.query).get(WR_ID_PARAM, [""])[0]
    if wr_id.isdigit():
        return f"{parsed.netloc}#{wr_id}"
    return fallback


@dataclass(frozen=True, slots=True)
class Article:
    key: str
    title: str
    href: str
    title_prefix: str
