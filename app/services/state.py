"""Pickle persistence for already-notified article keys."""

from __future__ import annotations

import pickle
from pathlib import Path

from app.models.article import article_key

ArticleState = dict[str, tuple[str, str]]


def load_state(path: Path) -> ArticleState:
    """Load state; a missing file starts empty, a corrupt file fails fast."""
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        state = pickle.load(handle)
    _validate_state(state, path)
    return _migrate_keys(state)


def _migrate_keys(state: ArticleState) -> ArticleState:
    """Rewrite legacy number-based keys to stable wr_id-based keys."""
    migrated: ArticleState = {}
    for key, value in state.items():
        migrated.setdefault(article_key(value[1], key), value)
    return migrated


def save_state(path: Path, state: ArticleState) -> None:
    _validate_state(state, path)
    with path.open("wb") as handle:
        pickle.dump(state, handle)


def _validate_state(state: object, path: Path) -> None:
    if not isinstance(state, dict):
        raise ValueError(f"invalid state in {path}: expected dict, got {type(state).__name__}")
    for key, value in state.items():
        valid_value = isinstance(value, tuple) and len(value) == 2
        valid_value = valid_value and all(isinstance(part, str) for part in value)
        if not isinstance(key, str) or not valid_value:
            raise ValueError(f"invalid state entry in {path}: {key!r}")
