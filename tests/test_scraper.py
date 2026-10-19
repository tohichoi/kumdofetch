"""Board parser against a small static fixture."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.scraper import parse_articles
from config.settings import SourceSettings

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "board.html"


def _source(table_index: int = 0) -> SourceSettings:
    return SourceSettings(
        name="center_notice",
        url="http://www.kumdo.org/bbs/board.php?bo_table=notice",
        table_index=table_index,
        title_prefix="[중앙:공지]",
    )


def test_parse_extracts_new_numeric_rows() -> None:
    html_bytes = FIXTURE_PATH.read_bytes()

    articles = parse_articles(html_bytes, _source(), known_keys=set())

    assert list(articles) == ["center_notice12", "center_notice11"]
    first = articles["center_notice12"]
    assert first.title == "제목 & 안내"
    assert first.href == "https://www.kumdo.org/bbs/board.php?bo_table=notice&wr_id=12"
    assert first.title_prefix == "[중앙:공지]"


def test_parse_skips_known_keys() -> None:
    html_bytes = FIXTURE_PATH.read_bytes()

    articles = parse_articles(html_bytes, _source(), known_keys={"center_notice12"})

    assert list(articles) == ["center_notice11"]


def test_parse_rejects_out_of_range_table_index() -> None:
    html_bytes = FIXTURE_PATH.read_bytes()

    with pytest.raises(ValueError, match="out of range"):
        parse_articles(html_bytes, _source(table_index=5), known_keys=set())


def test_parse_rejects_empty_html() -> None:
    with pytest.raises(ValueError, match="empty HTML"):
        parse_articles(b"", _source(), known_keys=set())
