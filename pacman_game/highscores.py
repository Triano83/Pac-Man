"""Persistent top 10 highscores stored in a JSON file."""
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MAX_ENTRIES = 10
MAX_NAME_LENGTH = 10
DEFAULT_NAME = "Player"


@dataclass
class HighscoreEntry:
    """One line of the highscore table."""

    name: str
    score: int


def is_valid_char(char: str) -> bool:
    """Return True for a character allowed in names: A-Z, a-z, 0-9, space."""
    return (char.isascii() and char.isalnum()) or char == " "


def is_valid_name(name: str) -> bool:
    """Return True if name respects every rule of the subject."""
    return (bool(name.strip()) and len(name) <= MAX_NAME_LENGTH
            and all(is_valid_char(char) for char in name))


def clean_name(raw: str) -> str:
    """Turn any text into a valid name.

    Invalid characters are removed, the result is cut to MAX_NAME_LENGTH
    characters and, if nothing is left, DEFAULT_NAME is used.
    """
    kept = "".join(char for char in raw if is_valid_char(char))
    kept = kept.strip()[:MAX_NAME_LENGTH].strip()
    return kept or DEFAULT_NAME


def _parse_entry(raw: Any) -> HighscoreEntry | None:
    """Convert one item of the file into an entry, or None if invalid."""
    if not isinstance(raw, dict):
        return None
    name = raw.get("name")
    score = raw.get("score")
    if not isinstance(name, str) or not is_valid_name(name):
        return None
    if isinstance(score, bool) or not isinstance(score, int) or score < 0:
        return None
    return HighscoreEntry(name, score)


class HighscoreManager:
    """Loads, updates and saves the top 10 scores."""

    def __init__(self, filename: str) -> None:
        """Create the manager; call load() to read the file."""
        self.path = Path(filename)
        self.entries: list[HighscoreEntry] = []

    def load(self) -> None:
        """Read the file. Any problem leaves a valid (maybe empty) table."""
        self.entries = []
        try:
            with self.path.open(encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            logger.info("No highscore file '%s' yet: starting empty",
                        self.path)
            return
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            logger.warning("Cannot read highscores from '%s' (%s): "
                           "starting empty", self.path, error)
            return
        if not isinstance(data, list):
            logger.warning("Highscore file '%s' has a wrong format: "
                           "starting empty", self.path)
            return
        for item in data:
            entry = _parse_entry(item)
            if entry is None:
                logger.warning("Ignoring invalid highscore entry: %r", item)
            else:
                self.entries.append(entry)
        self.entries.sort(key=lambda entry: entry.score, reverse=True)
        del self.entries[MAX_ENTRIES:]

    def qualifies(self, score: int) -> bool:
        """Return True if the score would enter the top 10."""
        if score <= 0:
            return False
        if len(self.entries) < MAX_ENTRIES:
            return True
        return score > self.entries[-1].score

    def add(self, name: str, score: int) -> int | None:
        """Insert a score in the table.

        Args:
            name: Player name; it is cleaned to respect the rules.
            score: Final score, a non-negative integer.

        Returns:
            The position (1 to 10) of the new entry, or None if the score
            did not reach the top 10.

        Raises:
            ValueError: If score is not a non-negative integer.
        """
        if isinstance(score, bool) or not isinstance(score, int) or score < 0:
            raise ValueError("score must be a non-negative integer")
        entry = HighscoreEntry(clean_name(name), score)
        position = len(self.entries)
        for index, other in enumerate(self.entries):
            if score > other.score:
                position = index
                break
        if position >= MAX_ENTRIES:
            return None
        self.entries.insert(position, entry)
        del self.entries[MAX_ENTRIES:]
        return position + 1

    def save(self) -> bool:
        """Write the table to disk. Return False if it could not be saved."""
        data = [{"name": entry.name, "score": entry.score}
                for entry in self.entries]
        temp_path = self.path.with_name(self.path.name + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with temp_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)
            os.replace(temp_path, self.path)
        except OSError as error:
            logger.warning("Cannot save highscores to '%s': %s",
                           self.path, error)
            return False
        return True
