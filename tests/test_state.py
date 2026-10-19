"""Pickle state persistence and validation."""

from __future__ import annotations

import pickle
from pathlib import Path

import pytest

from app.services.state import load_state, save_state


def test_missing_file_returns_empty_state(tmp_path: Path) -> None:
    assert load_state(tmp_path / "state.pickle") == {}


def test_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "state.pickle"
    state = {"center_notice1": ("공지 제목", "https://www.kumdo.org/1")}

    save_state(path, state)

    assert load_state(path) == state


def test_corrupt_pickle_raises(tmp_path: Path) -> None:
    path = tmp_path / "state.pickle"
    path.write_bytes(b"not a pickle")

    with pytest.raises(pickle.UnpicklingError):
        load_state(path)


def test_wrong_top_level_type_raises(tmp_path: Path) -> None:
    path = tmp_path / "state.pickle"
    path.write_bytes(pickle.dumps(["not", "a", "dict"]))

    with pytest.raises(ValueError, match="expected dict"):
        load_state(path)


def test_wrong_entry_type_raises(tmp_path: Path) -> None:
    path = tmp_path / "state.pickle"
    path.write_bytes(pickle.dumps({"center_notice1": ["title", "href"]}))

    with pytest.raises(ValueError, match="invalid state entry"):
        load_state(path)


def test_save_rejects_invalid_state(tmp_path: Path) -> None:
    path = tmp_path / "state.pickle"

    with pytest.raises(ValueError, match="invalid state entry"):
        save_state(path, {"center_notice1": ("제목",)})

    assert not path.exists()
