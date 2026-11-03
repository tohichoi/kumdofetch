"""Board scraping: fetch HTML and extract new article links."""

from __future__ import annotations

import logging
import urllib.request

from bs4 import BeautifulSoup

from app.models.article import Article, article_key
from config.settings import SourceSettings

LOGGER = logging.getLogger(__name__)

MIN_ROW_CELLS = 2


def fetch_html(url: str, timeout_seconds: float) -> bytes:
    """Fetch board HTML with an explicit timeout (no retry fallback)."""
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"unsupported URL scheme: {url}")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
        return response.read()


def parse_articles(
    html_bytes: bytes, source: SourceSettings, known_keys: set[str]
) -> dict[str, Article]:
    """Extract new rows from the configured table index."""
    if not html_bytes:
        raise ValueError(f"empty HTML response for source {source.name}")

    soup = BeautifulSoup(html_bytes, "html.parser")
    tables = soup.find_all("table")
    if source.table_index >= len(tables):
        raise ValueError(
            f"source {source.name}: table_index {source.table_index} "
            f"out of range (found {len(tables)} tables)"
        )

    articles: dict[str, Article] = {}
    for row in tables[source.table_index].find_all("tr"):
        article = _parse_row(row, source, known_keys)
        if article is not None:
            articles.setdefault(article.key, article)
    return articles


def collect_new_articles(
    sources: list[SourceSettings],
    known_keys: set[str],
    timeout_seconds: float,
    max_pages: int = 1,
) -> dict[str, Article]:
    """Fetch and parse the first `max_pages` pages of every configured source."""
    new_articles: dict[str, Article] = {}
    for source in sources:
        for page in range(1, max_pages + 1):
            new_articles.update(
                parse_articles(fetch_html(_page_url(source.url, page), timeout_seconds),
                               source, known_keys)
            )
    return new_articles


def _page_url(url: str, page: int) -> str:
    if page == 1:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}page={page}"


def _parse_row(row, source: SourceSettings, known_keys: set[str]) -> Article | None:
    cells = row.find_all("td")
    if len(cells) < MIN_ROW_CELLS:
        if cells:
            LOGGER.error("malformed row in %s: %s", source.name, row)
        return None

    number = cells[0].text.strip()
    link = cells[1].find("a")
    href = str(link["href"]).strip() if link is not None and link.get("href") else ""
    key = article_key(href, f"{source.name}{number}")
    if key in known_keys:
        return None
    if not href:
        if number.isnumeric():
            raise ValueError(f"source {source.name}: article {key} has no link")
        return None
    return Article(
        key=key,
        title=cells[1].text.strip(),
        href=href,
        title_prefix=source.title_prefix,
    )
