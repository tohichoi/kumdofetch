"""Board scraping: fetch HTML and extract new article links."""

from __future__ import annotations

import logging
import re
import urllib.request
from datetime import date

from bs4 import BeautifulSoup

from app.models.article import Article, article_key
from config.settings import SourceSettings

LOGGER = logging.getLogger(__name__)

MIN_ROW_CELLS = 2
DATE_PATTERN = re.compile(r"^(\d{4}|\d{2})-(\d{2})-(\d{2})$")
SHORT_DATE_PATTERN = re.compile(r"^(\d{2})-(\d{2})$")


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
        date=parse_post_date(row),
    )


def parse_post_date(row) -> str:
    """Return the first date-looking cell as ISO (YYYY-MM-DD), else ''."""
    today = date.today()
    for cell in row.find_all("td")[2:]:
        parsed = _parse_date_cell(cell.text.strip(), today)
        if parsed:
            return parsed
    return ""


def _parse_date_cell(text: str, today: date) -> str:
    match = DATE_PATTERN.match(text)
    if match:
        year, month, day = match.groups()
        full_year = int(year) + 2000 if len(year) == 2 else int(year)
        return _iso_date(full_year, int(month), int(day))

    match = SHORT_DATE_PATTERN.match(text)
    if match:
        month, day = (int(part) for part in match.groups())
        year = today.year if month <= today.month else today.year - 1
        return _iso_date(year, month, day)
    return ""


def _iso_date(year: int, month: int, day: int) -> str:
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return ""
