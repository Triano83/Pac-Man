"""Loading and validation of the game configuration file."""
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

COMMENT_PREFIXES = ("#", "//")
MIN_LEVELS = 10
MIN_SIZE = 14
MAX_SIZE = 50


class ConfigError(Exception):
    """Raised when the configuration file cannot be used at all."""


@dataclass
class LevelConfig:
    """Size of the maze of one level."""

    width: int = 20
    height: int = 20


def _default_levels() -> list[LevelConfig]:
    """Return the default list of levels."""
    return [LevelConfig() for _ in range(MIN_LEVELS)]


@dataclass
class GameConfig:
    """All the game parameters, with safe default values."""

    highscore_filename: str = "highscores.json"
    levels: list[LevelConfig] = field(default_factory=_default_levels)
    lives: int = 3
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    seed: int = 42
    level_max_time: int = 90


def strip_comments(text: str) -> str:
    """Blank out comment lines, keeping the line numbers unchanged."""
    lines = []
    for line in text.splitlines():
        if line.lstrip().startswith(COMMENT_PREFIXES):
            line = ""
        lines.append(line)
    return "\n".join(lines)


def _read_int(data: dict[str, Any], key: str, default: int,
              minimum: int, maximum: int) -> int:
    """Read an integer from data, clamped to [minimum, maximum]."""
    if key not in data:
        logger.warning("Missing key '%s': using default %d", key, default)
        return default
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int):
        logger.warning("Invalid value for '%s' (expected an integer): "
                       "using default %d", key, default)
        return default
    if value < minimum or value > maximum:
        clamped = max(minimum, min(value, maximum))
        logger.warning("Value %d for '%s' is out of range [%d, %d]: "
                       "using %d", value, key, minimum, maximum, clamped)
        return clamped
    return value


def _read_str(data: dict[str, Any], key: str, default: str) -> str:
    """Read a non-empty string from data."""
    if key not in data:
        logger.warning("Missing key '%s': using default '%s'", key, default)
        return default
    value = data[key]
    if not isinstance(value, str) or not value.strip():
        logger.warning("Invalid value for '%s' (expected a non-empty "
                       "string): using default '%s'", key, default)
        return default
    return value.strip()


def _read_levels(data: dict[str, Any]) -> list[LevelConfig]:
    """Read the list of levels, completing it up to MIN_LEVELS."""
    raw = data.get("level")
    if not isinstance(raw, list) or not raw:
        logger.warning("Missing or invalid 'level' array: using %d "
                       "default levels", MIN_LEVELS)
        return _default_levels()
    levels: list[LevelConfig] = []
    for index, entry in enumerate(raw, start=1):
        if not isinstance(entry, dict):
            logger.warning("Level %d is not an object: using defaults",
                           index)
            levels.append(LevelConfig())
            continue
        levels.append(LevelConfig(
            width=_read_int(entry, "width", 20, MIN_SIZE, MAX_SIZE),
            height=_read_int(entry, "height", 20, MIN_SIZE, MAX_SIZE)))
    if len(levels) < MIN_LEVELS:
        logger.warning("Only %d levels defined: adding default levels "
                       "up to %d", len(levels), MIN_LEVELS)
        levels.extend(LevelConfig()
                      for _ in range(MIN_LEVELS - len(levels)))
    return levels


def load_config(path: str) -> GameConfig:
    """Load and validate the configuration file.

    Args:
        path: Path of the JSON configuration file.

    Returns:
        The validated game configuration.

    Raises:
        ConfigError: If the file is missing, unreadable or not valid JSON.
    """
    file_path = Path(path)
    if file_path.suffix.lower() != ".json":
        raise ConfigError(f"'{path}' is not a .json file")
    try:
        with file_path.open(encoding="utf-8") as file:
            text = file.read()
    except FileNotFoundError:
        raise ConfigError(f"File '{path}' not found") from None
    except UnicodeDecodeError:
        raise ConfigError(f"File '{path}' is not valid UTF-8 text") from None
    except OSError as error:
        raise ConfigError(f"Cannot read '{path}': {error.strerror}") from error
    try:
        data = json.loads(strip_comments(text))
    except json.JSONDecodeError as error:
        raise ConfigError(
            f"Invalid JSON in '{path}': {error.msg} "
            f"(line {error.lineno}, column {error.colno})") from error
    if not isinstance(data, dict):
        raise ConfigError("The top level of the config must be an object")
    return GameConfig(
        highscore_filename=_read_str(data, "highscore_filename",
                                     "highscores.json"),
        levels=_read_levels(data),
        lives=_read_int(data, "lives", 3, 1, 99),
        points_per_pacgum=_read_int(data, "points_per_pacgum",
                                    10, 0, 10000),
        points_per_super_pacgum=_read_int(data, "points_per_super_pacgum",
                                          50, 0, 10000),
        points_per_ghost=_read_int(data, "points_per_ghost",
                                   200, 0, 10000),
        seed=_read_int(data, "seed", 42, 1, 2**31 - 1),
        level_max_time=_read_int(data, "level_max_time", 90, 10, 3600),
    )
