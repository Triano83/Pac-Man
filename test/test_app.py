"""Tests for the application: scenes, keys and drawing (no real window)."""
from collections.abc import Iterator
from pathlib import Path

import pytest

from pacman_game import app as app_module
from pacman_game.app import App, Scene
from pacman_game.config import GameConfig
from pacman_game.entities import Direction, GhostState
from pacman_game.game import GameState
from pacman_game.highscores import HighscoreManager
from pacman_game.maze import MazeError
from pacman_game.renderer import KeyEvent, QuitEvent, Renderer
from pacman_game.sprites import SpriteFactory
from pacman_game.views import WINDOW_HEIGHT, WINDOW_WIDTH

SOURCE_FILES = sorted(Path(app_module.__file__).parent.glob("*.py"))


@pytest.fixture
def renderer() -> Iterator[Renderer]:
    """A window that is closed at the end of the test."""
    window = Renderer(WINDOW_WIDTH, WINDOW_HEIGHT, "test")
    yield window
    window.close()


@pytest.fixture
def app(renderer: Renderer, tmp_path: Path) -> App:
    """An application with an empty highscore file in a temp folder."""
    scores = HighscoreManager(str(tmp_path / "scores.json"))
    return App(GameConfig(), renderer, scores)


def press(app: App, *names: str) -> None:
    """Press several keys; one letter keys also type that letter."""
    for name in names:
        char = name if len(name) == 1 else ""
        app.handle_event(KeyEvent(name, char))


def start(app: App) -> None:
    """Start a game from the main menu."""
    press(app, "enter")
    assert app.scene == Scene.GAME


def run_time(app: App, seconds: float) -> None:
    """Let the application run for some seconds."""
    for _ in range(round(seconds / 0.05)):
        app.update(0.05)


def test_only_the_renderer_uses_pygame() -> None:
    """Nothing but renderer.py imports pygame (MLX-like restriction)."""
    for path in SOURCE_FILES:
        if path.name == "renderer.py":
            continue
        assert "pygame" not in path.read_text(encoding="utf-8"), path.name


def test_every_scene_can_be_drawn(app: App) -> None:
    """Drawing each screen does not fail."""
    app.draw(0.0)
    press(app, "down", "enter")
    assert app.scene == Scene.HIGHSCORES
    app.draw(0.0)
    press(app, "escape", "down", "enter")
    assert app.scene == Scene.INSTRUCTIONS
    app.draw(0.0)
    press(app, "escape", "up", "up")
    start(app)
    app.draw(0.0)
    run_time(app, 3.0)
    app.draw(1.0)
    press(app, "escape")
    app.draw(1.0)


def test_menu_navigation_wraps(app: App) -> None:
    """The selection goes around the menu."""
    press(app, "up")
    assert app.menu_index == 3
    press(app, "down")
    assert app.menu_index == 0
    press(app, "s", "w")
    assert app.menu_index == 0


def test_menu_exit_and_window_close(app: App) -> None:
    """The Exit item and the window close button stop the app."""
    press(app, "up", "enter")
    assert not app.running
    app.running = True
    app.handle_event(QuitEvent())
    assert not app.running


def test_space_starts_the_game(app: App) -> None:
    """SPACE on the first menu item starts a game."""
    press(app, "space")
    assert app.scene == Scene.GAME


def test_player_is_controlled_with_keys(app: App) -> None:
    """Arrow keys and WASD set the wanted direction."""
    start(app)
    assert app.game is not None
    for key, direction in (("up", Direction.UP), ("a", Direction.LEFT),
                           ("s", Direction.DOWN), ("right", Direction.RIGHT)):
        press(app, key)
        assert app.game.player.wanted == direction


def test_pause_and_resume(app: App) -> None:
    """ESC pauses, ESC again resumes; the menu offers both options."""
    start(app)
    assert app.game is not None
    press(app, "escape")
    assert app.game.paused
    app.draw(0.0)
    press(app, "enter")
    assert not app.game.paused
    press(app, "p")
    assert app.game.paused
    press(app, "p")
    assert not app.game.paused


def test_pause_menu_returns_to_main_menu(app: App) -> None:
    """The second item of the pause menu leaves the game."""
    start(app)
    press(app, "escape", "down", "enter")
    assert app.scene == Scene.MENU
    assert app.game is None


def test_cheat_keys(app: App) -> None:
    """C turns on the cheat mode and the digits use the cheats."""
    start(app)
    game = app.game
    assert game is not None
    press(app, "1", "4")
    assert not game.invincible and game.lives == 3
    press(app, "c", "1", "2", "3", "4", "6")
    assert game.invincible and game.ghosts_frozen and game.fast_player
    assert game.lives == 4
    assert all(g.state == GhostState.FRIGHTENED for g in game.ghosts)
    app.draw(0.0)
    press(app, "5")
    assert game.level_number == 2
    assert app.banner == "Level complete!"
    app.draw(0.0)
    press(app, "c")
    assert not game.cheat_mode


def test_game_over_to_highscore(app: App) -> None:
    """Losing the last life asks for a name, saves it and shows the menu."""
    start(app)
    game = app.game
    assert game is not None
    game.ready_timer = 0.0
    game.lives = 1
    game.player.wanted = Direction.NONE
    game.ghosts[0].place(*game.player.cell)
    game._check_collisions([])
    assert game.state == GameState.GAME_OVER
    app.update(0.0)
    assert app.scene == Scene.NAME_ENTRY
    assert app.end_title == "GAME OVER"
    app.draw(0.0)
    press(app, "a", "n", "a")
    press(app, "enter")
    assert app.scene == Scene.MENU
    assert [e.name for e in app.highscores.entries] == ["ana"]
    assert app.notice.startswith("New highscore")
    reloaded = HighscoreManager(str(app.highscores.path))
    reloaded.load()
    assert reloaded.entries == app.highscores.entries
    app.draw(0.0)


def test_victory_screen(app: App) -> None:
    """Finishing all levels shows the victory screen."""
    start(app)
    game = app.game
    assert game is not None
    press(app, "c")
    for _ in range(game.total_levels):
        press(app, "5")
    assert game.state == GameState.VICTORY
    app.update(0.0)
    assert app.scene == Scene.NAME_ENTRY
    assert app.end_title == "VICTORY!"
    app.draw(0.0)
    press(app, "escape")
    assert app.scene == Scene.MENU
    assert app.highscores.entries == []


def test_name_entry_filters_characters(app: App) -> None:
    """Only valid characters are accepted, up to 10, and backspace works."""
    app.scene = Scene.NAME_ENTRY
    app.final_score = 100
    app.handle_event(KeyEvent("!", "!"))
    app.handle_event(KeyEvent("enter", ""))
    assert app.scene == Scene.MENU
    assert app.highscores.entries[0].name == "Player"
    app.scene = Scene.NAME_ENTRY
    app.name_text = ""
    for char in "abcdefghijklmnop":
        press(app, char)
    assert app.name_text == "abcdefghij"
    press(app, "backspace")
    assert app.name_text == "abcdefghi"
    app.handle_event(KeyEvent("space", " "))
    assert app.name_text == "abcdefghi "


def test_maze_error_at_start_shows_a_message(
        app: App, monkeypatch: pytest.MonkeyPatch) -> None:
    """If the generator fails the menu explains it; nothing crashes."""
    def broken(config: GameConfig) -> None:
        raise MazeError("generator exploded")

    monkeypatch.setattr(app_module, "Game", broken)
    press(app, "enter")
    assert app.scene == Scene.MENU
    assert "generator exploded" in app.error
    app.draw(0.0)
    press(app, "down")
    assert app.error == ""


def raise_maze_error() -> None:
    """Stand-in for a level builder that always fails."""
    raise MazeError("no more mazes")


def test_maze_error_when_skipping_a_level(app: App) -> None:
    """A failure while building the next level goes back to the menu."""
    start(app)
    assert app.game is not None
    app.game._start_level = raise_maze_error  # type: ignore[method-assign]
    press(app, "c", "5")
    assert app.scene == Scene.MENU
    assert "no more mazes" in app.error
    app.draw(0.0)


def test_maze_error_when_finishing_a_level(app: App) -> None:
    """The same, when the level ends by eating the last pellet."""
    start(app)
    game = app.game
    assert game is not None
    game.ready_timer = 0.0
    target = game.maze.neighbors(*game.player.cell)[0]
    direction = next(d for d in (Direction.UP, Direction.DOWN,
                                 Direction.LEFT, Direction.RIGHT)
                     if (game.player.x + d.dx,
                         game.player.y + d.dy) == target)
    game.pacgums = {target}
    game.super_pacgums = set()
    game._start_level = raise_maze_error  # type: ignore[method-assign]
    press(app, {Direction.UP: "up", Direction.DOWN: "down",
                Direction.LEFT: "left", Direction.RIGHT: "right"}[direction])
    run_time(app, 0.5)
    assert app.scene == Scene.MENU
    assert "no more mazes" in app.error


def test_sprites_have_pixels(renderer: Renderer) -> None:
    """The pictures are drawn and are not empty."""
    factory = SpriteFactory(renderer, 24)
    pictures = [factory.pacman(Direction.LEFT, 2), factory.pacgum(),
                factory.super_pacgum(),
                factory.ghost("Inky", "normal", (1, 0)),
                factory.ghost("Clyde", "scared", (0, 0)),
                factory.ghost("Pinky", "flash", (0, 0)),
                factory.ghost("Blinky", "eyes", (0, 1))]
    for picture in pictures:
        assert (picture.width, picture.height) == (24, 24)
        assert picture._surface.get_bounding_rect().width > 0
    assert factory.pacman(Direction.LEFT, 2) is pictures[0]


def test_different_maze_sizes_fit_the_window(app: App) -> None:
    """The view chooses a cell size that fits the biggest allowed maze."""
    from pacman_game.config import LevelConfig
    levels = [LevelConfig(50, 50)] * 10
    config = GameConfig(levels=levels)
    scores = HighscoreManager(str(app.highscores.path))
    big = App(config, app.renderer, scores)
    start(big)
    assert big.view is not None
    assert big.view.cell * 50 <= WINDOW_WIDTH
    big.draw(0.0)
