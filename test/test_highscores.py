"""Tests for the highscore system."""
import json
from pathlib import Path

import pytest

from pacman_game.highscores import (MAX_ENTRIES, HighscoreManager,
                                    clean_name, is_valid_name)


def make_manager(tmp_path: Path) -> HighscoreManager:
    """Return a manager that stores its file inside tmp_path."""
    return HighscoreManager(str(tmp_path / "scores.json"))


def test_missing_file_starts_empty(tmp_path: Path) -> None:
    """A missing file is not an error."""
    manager = make_manager(tmp_path)
    manager.load()
    assert manager.entries == []


@pytest.mark.parametrize("content", ["", "not json", "{}", "42",
                                     '[{"name": 1}]', "[1, 2, 3]"])
def test_corrupted_file_starts_empty(tmp_path: Path, content: str) -> None:
    """Any broken file gives an empty but valid table."""
    manager = make_manager(tmp_path)
    manager.path.write_text(content, encoding="utf-8")
    manager.load()
    assert manager.entries == []


def test_directory_instead_of_file(tmp_path: Path) -> None:
    """A directory with the file name does not crash the game."""
    manager = make_manager(tmp_path)
    manager.path.mkdir()
    manager.load()
    assert manager.entries == []
    assert manager.save() is False


def test_invalid_entries_are_skipped(tmp_path: Path) -> None:
    """Only the valid lines of a damaged file are kept."""
    manager = make_manager(tmp_path)
    data = [{"name": "Ana", "score": 100},
            {"name": "Bad!name", "score": 50},
            {"name": "Neg", "score": -5},
            {"name": "Flt", "score": 2.5},
            {"name": "Bob", "score": 300}]
    manager.path.write_text(json.dumps(data), encoding="utf-8")
    manager.load()
    assert [(e.name, e.score) for e in manager.entries] == [
        ("Bob", 300), ("Ana", 100)]


def test_table_is_sorted_and_limited(tmp_path: Path) -> None:
    """Only the 10 best scores are kept, in descending order."""
    manager = make_manager(tmp_path)
    for score in range(1, 16):
        manager.add("P", score * 10)
    assert len(manager.entries) == MAX_ENTRIES
    scores = [entry.score for entry in manager.entries]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] == 150 and scores[-1] == 60


def test_add_returns_position(tmp_path: Path) -> None:
    """add() tells where the score landed, or None if it did not enter."""
    manager = make_manager(tmp_path)
    assert manager.add("A", 100) == 1
    assert manager.add("B", 200) == 1
    assert manager.add("C", 150) == 2
    for _ in range(MAX_ENTRIES):
        manager.add("Z", 1000)
    assert manager.add("Low", 5) is None


def test_equal_scores_keep_older_first(tmp_path: Path) -> None:
    """On a tie the older entry stays above the new one."""
    manager = make_manager(tmp_path)
    manager.add("First", 100)
    manager.add("Second", 100)
    assert [e.name for e in manager.entries] == ["First", "Second"]


def test_qualifies(tmp_path: Path) -> None:
    """Zero never qualifies; a full table needs a better score."""
    manager = make_manager(tmp_path)
    assert not manager.qualifies(0)
    assert manager.qualifies(1)
    for _ in range(MAX_ENTRIES):
        manager.add("Z", 100)
    assert not manager.qualifies(100)
    assert manager.qualifies(101)


@pytest.mark.parametrize("score", [-1, 1.5, "10", None, True])
def test_bad_score_is_rejected(tmp_path: Path, score: object) -> None:
    """Scores must be non-negative integers."""
    manager = make_manager(tmp_path)
    with pytest.raises(ValueError):
        manager.add("A", score)  # type: ignore[arg-type]


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    """What is saved is what is loaded."""
    manager = make_manager(tmp_path)
    manager.add("Ana", 500)
    manager.add("Luis", 700)
    assert manager.save() is True
    other = make_manager(tmp_path)
    other.load()
    assert other.entries == manager.entries
    assert not manager.path.with_name("scores.json.tmp").exists()


def test_save_creates_missing_folder(tmp_path: Path) -> None:
    """The folder of the file is created if needed."""
    manager = HighscoreManager(str(tmp_path / "sub" / "dir" / "s.json"))
    manager.add("Ana", 10)
    assert manager.save() is True


@pytest.mark.parametrize("raw, expected", [
    ("Ana", "Ana"),
    ("  Ana  ", "Ana"),
    ("a_b-c!", "abc"),
    ("ABCDEFGHIJKLMNOP", "ABCDEFGHIJ"),
    ("Jose Luis", "Jose Luis"),
    ("ñandú", "and"),
    ("", "Player"),
    ("!!!", "Player"),
    ("   ", "Player"),
])
def test_clean_name(raw: str, expected: str) -> None:
    """Names are cleaned to respect the subject rules."""
    result = clean_name(raw)
    assert result == expected
    assert is_valid_name(result)


def test_is_valid_name() -> None:
    """Direct validation of names."""
    assert is_valid_name("Ana 1")
    assert not is_valid_name("")
    assert not is_valid_name("   ")
    assert not is_valid_name("12345678901")
    assert not is_valid_name("a-b")
