"""Article data model shared by scraper, state and message rendering."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Article:
    key: str
    title: str
    href: str
    title_prefix: str
