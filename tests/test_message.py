"""Message rendering, chunking and title truncation."""

from __future__ import annotations

import logging

import pytest

from app.models.article import Article
from app.views.message import render_messages


def _article(index: int, title: str | None = None, href: str | None = None) -> Article:
    return Article(
        key=f"center_notice{index}",
        title=title or f"공지 제목 {index}",
        href=href or f"https://www.kumdo.org/bbs/board.php?wr_id={index}",
        title_prefix="[중앙:공지]",
    )


def test_render_escapes_title_and_href() -> None:
    article = Article(
        key="center_notice1",
        title="제목 & 안내",
        href="https://www.kumdo.org/?a=1&b=2",
        title_prefix="[중앙:공지]",
    )

    messages = render_messages([article], 4096)

    assert messages == [
        '[중앙:공지] <a href="https://www.kumdo.org/?a=1&amp;b=2">제목 &amp; 안내</a>\n'
    ]


def test_render_splits_at_max_chars() -> None:
    articles = [_article(index, "제목 " + "가" * 40) for index in range(10)]

    messages = render_messages(articles, 150)

    assert len(messages) > 1
    assert all(len(message) <= 150 for message in messages)
    assert "".join(messages) == "".join(
        f'[중앙:공지] <a href="{article.href}">{article.title}</a>\n' for article in articles
    )


def test_render_truncates_oversized_title(caplog: pytest.LogCaptureFixture) -> None:
    article = _article(1, "가" * 200)

    with caplog.at_level(logging.WARNING):
        messages = render_messages([article], 100)

    assert len(messages) == 1
    assert len(messages[0]) <= 100
    assert messages[0].endswith("…</a>\n")
    assert "truncating title" in caplog.text


@pytest.mark.parametrize(
    "href",
    ["javascript:alert(1)", "data:text/html,x", "tg://resolve?domain=x", "mailto:a@example.com"],
)
def test_render_rejects_unsafe_scheme(href: str) -> None:
    with pytest.raises(ValueError, match="unsafe href"):
        render_messages([_article(1, href=href)], 4096)


def test_render_allows_relative_href() -> None:
    messages = render_messages([_article(1, href="bbs/board.php?bo_table=notice")], 4096)

    assert 'href="bbs/board.php?bo_table=notice"' in messages[0]


def test_render_rejects_non_positive_limit() -> None:
    with pytest.raises(ValueError, match="positive"):
        render_messages([_article(1)], 0)
