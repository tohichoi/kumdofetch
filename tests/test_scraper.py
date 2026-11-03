"""Board parser against a small static fixture."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.scraper import parse_articles
from config.settings import SourceSettings

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "board.html"
SNKUMDO_PATH = Path(__file__).parent / "fixtures" / "snkumdo.html"


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

    assert list(articles) == ["www.kumdo.org#12", "www.kumdo.org#11"]
    first = articles["www.kumdo.org#12"]
    assert first.title == "제목 & 안내"
    assert first.href == "https://www.kumdo.org/bbs/board.php?bo_table=notice&wr_id=12"
    assert first.title_prefix == "[중앙:공지]"
    assert first.date == "2026-10-19"


def test_parse_skips_known_keys() -> None:
    html_bytes = FIXTURE_PATH.read_bytes()

    articles = parse_articles(html_bytes, _source(), known_keys={"www.kumdo.org#12"})

    assert list(articles) == ["www.kumdo.org#11"]


def test_parse_collects_pinned_notice_rows() -> None:
    html_bytes = (
        "<table><tr><td>공지</td>"
        '<td><a href="https://www.kumdo.org/bbs/board.php?wr_id=99">고정 공지</a></td></tr></table>'
    ).encode()

    articles = parse_articles(html_bytes, _source(), known_keys=set())

    assert list(articles) == ["www.kumdo.org#99"]


def test_parse_reads_short_month_day_dates() -> None:
    html_bytes = (
        "<table><tr><td>공지</td>"
        '<td><a href="https://ti.kumdo.org/bbs/board.php?wr_id=7">강습회</a></td>'
        "<td>연수원</td><td>523</td><td>10-26</td></tr></table>"
    ).encode()

    articles = parse_articles(html_bytes, _source(), known_keys=set())

    assert articles["ti.kumdo.org#7"].date.endswith("-10-26")
    assert len(articles["ti.kumdo.org#7"].date) == 10


def test_parse_resolves_relative_links_and_skips_separator_rows() -> None:
    source = SourceSettings(
        name="sn_notice",
        url="http://www.snkumdo.co.kr/dmboard/list.php?board=sungnamsi06",
        table_index=0,
        title_prefix="[성남:공지]",
    )

    articles = parse_articles(SNKUMDO_PATH.read_bytes(), source, known_keys=set())

    assert list(articles) == [
        "www.snkumdo.co.kr#sungnamsi06#427",
        "www.snkumdo.co.kr#sungnamsi06#442",
    ]
    assert articles["www.snkumdo.co.kr#sungnamsi06#442"].href == (
        "http://www.snkumdo.co.kr/dmboard/read.php"
        "?board=sungnamsi06&md=4&mode=view&idx=442&search=&searchstring=&page=1"
    )
    assert articles["www.snkumdo.co.kr#sungnamsi06#442"].date == "2026-10-28"


def test_parse_rejects_out_of_range_table_index() -> None:
    html_bytes = FIXTURE_PATH.read_bytes()

    with pytest.raises(ValueError, match="out of range"):
        parse_articles(html_bytes, _source(table_index=5), known_keys=set())


def test_parse_rejects_empty_html() -> None:
    with pytest.raises(ValueError, match="empty HTML"):
        parse_articles(b"", _source(), known_keys=set())
