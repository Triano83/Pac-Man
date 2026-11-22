"""Command line part of the game: arguments, errors and start-up."""
import logging
import os
import sys

from pacman_game.app import App
from pacman_game.config import ConfigError, load_config
from pacman_game.highscores import HighscoreManager
from pacman_game.renderer import Renderer, RendererError
from pacman_game.views import WINDOW_HEIGHT, WINDOW_WIDTH


def run(config_path: str) -> int:
    """Load the configuration and play; return the exit code."""
    try:
        config = load_config(config_path)
    except ConfigError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    highscores = HighscoreManager(config.highscore_filename)
    highscores.load()
    try:
        renderer = Renderer(WINDOW_WIDTH, WINDOW_HEIGHT, "Pac-Man")
    except RendererError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    try:
        App(config, renderer, highscores).run()
    finally:
        renderer.close()
    return 0


def main() -> int:
    """Check the arguments and run the game without ever showing a traceback.

    Set the environment variable PACMAN_DEBUG=1 to see the full error.
    """
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s: %(message)s")
    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py <config.json>", file=sys.stderr)
        return 1
    try:
        return run(sys.argv[1])
    except KeyboardInterrupt:
        return 0
    except Exception as error:  # last barrier: the game must not crash
        if os.environ.get("PACMAN_DEBUG"):
            raise
        print(f"Unexpected error: {error}", file=sys.stderr)
        return 1
