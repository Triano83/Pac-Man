"""Starts the packaged game: it needs no command line argument."""
import os
import sys
from pathlib import Path

from pacman_game.cli import main


def game_folder() -> Path:
    """Return the folder where the game (or this script) lives."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def start() -> int:
    """Use the config.json next to the game when no argument is given."""
    for name in ("stdout", "stderr"):
        if getattr(sys, name) is None:  # windowed apps have no console
            setattr(sys, name, open(os.devnull, "w", encoding="utf-8"))
    folder = game_folder()
    os.chdir(folder)
    if len(sys.argv) == 1:
        sys.argv.append(str(folder / "config.json"))
    return main()


if __name__ == "__main__":
    sys.exit(start())
