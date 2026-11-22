"""The application: menus, scenes and the main loop."""
import logging
import time
from enum import Enum

from pacman_game.config import GameConfig
from pacman_game.entities import Direction
from pacman_game.game import Game, GameEvent, GameState
from pacman_game.highscores import (MAX_ENTRIES, MAX_NAME_LENGTH,
                                    HighscoreManager, is_valid_char)
from pacman_game.maze import MazeError
from pacman_game.renderer import (Color, InputEvent, KeyEvent, QuitEvent,
                                  Renderer)
from pacman_game.views import (BACKGROUND, TEXT, WINDOW_HEIGHT, WINDOW_WIDTH,
                               GameView, draw_panel)

logger = logging.getLogger(__name__)

FPS = 60
CENTER = WINDOW_WIDTH // 2
YELLOW: Color = (255, 238, 0)
RED: Color = (255, 60, 60)
GREEN: Color = (80, 255, 80)
GREY: Color = (170, 170, 180)

MENU_ITEMS = ("Start Game", "View Highscores", "Instructions", "Exit")
PAUSE_ITEMS = ("Resume", "Return to main menu")
DIRECTION_KEYS = {
    "up": Direction.UP, "w": Direction.UP, "z": Direction.UP,
    "down": Direction.DOWN, "s": Direction.DOWN,
    "left": Direction.LEFT, "a": Direction.LEFT, "q": Direction.LEFT,
    "right": Direction.RIGHT, "d": Direction.RIGHT,
}
INSTRUCTIONS = (
    ("Controls", YELLOW),
    ("Arrow keys or WASD: move", TEXT),
    ("P or ESC: pause", TEXT),
    ("C: cheat mode (for reviewers)", TEXT),
    ("", TEXT),
    ("Rules", YELLOW),
    ("Eat all the pacgums to finish the level", TEXT),
    ("Super-pacgums make the ghosts edible for a while", TEXT),
    ("A ghost that touches you takes one life", TEXT),
    ("You also lose a life when the time of a level ends", TEXT),
    ("Lives and score are kept from level to level", TEXT),
    ("Finish every level to win the game", TEXT),
)
BANNERS = {
    GameEvent.LEVEL_COMPLETE: "Level complete!",
    GameEvent.LIFE_LOST: "Ouch!",
    GameEvent.TIME_UP: "Time up!",
}


class Scene(Enum):
    """The screens of the application."""

    MENU = "menu"
    HIGHSCORES = "highscores"
    INSTRUCTIONS = "instructions"
    GAME = "game"
    NAME_ENTRY = "name entry"


class App:
    """Connects the user (keys, window) with the game rules."""

    def __init__(self, config: GameConfig, renderer: Renderer,
                 highscores: HighscoreManager) -> None:
        """Create the application, showing the main menu."""
        self.config = config
        self.renderer = renderer
        self.highscores = highscores
        self.running = True
        self.scene = Scene.MENU
        self.menu_index = 0
        self.pause_index = 0
        self.game: Game | None = None
        self.view: GameView | None = None
        self.banner = ""
        self.error = ""
        self.notice = ""
        self.end_title = ""
        self.final_score = 0
        self.name_text = ""

    # ----- main loop -----

    def run(self) -> None:
        """Run until the user exits."""
        last = time.perf_counter()
        while self.running:
            frame_start = time.perf_counter()
            for event in self.renderer.poll_events():
                self.handle_event(event)
            self.update(frame_start - last)
            last = frame_start
            self.draw(frame_start)
            self.renderer.present()
            spent = time.perf_counter() - frame_start
            self.renderer.sleep(1 / FPS - spent)

    def update(self, dt: float) -> None:
        """Advance the game when it is being played."""
        game = self.game
        if self.scene != Scene.GAME or game is None:
            return
        try:
            events = game.update(dt)
        except MazeError as error:
            self._abort_game(f"The game stopped: {error}")
            return
        for event in events:
            if event in BANNERS:
                self.banner = BANNERS[event]
        if GameEvent.TIME_UP in events:
            self.banner = BANNERS[GameEvent.TIME_UP]
        if game.ready_timer <= 0 and game.state == GameState.PLAYING:
            self.banner = ""
        if game.state != GameState.PLAYING:
            self._finish_game(game)

    # ----- input -----

    def handle_event(self, event: InputEvent) -> None:
        """React to a key press or to the closing of the window."""
        if isinstance(event, QuitEvent):
            self.running = False
            return
        if not isinstance(event, KeyEvent):
            return
        if self.scene == Scene.MENU:
            self._key_menu(event)
        elif self.scene in (Scene.HIGHSCORES, Scene.INSTRUCTIONS):
            if event.name in ("escape", "enter", "space"):
                self._to_menu()
        elif self.scene == Scene.GAME:
            self._key_game(event)
        elif self.scene == Scene.NAME_ENTRY:
            self._key_name(event)

    def _move_selection(self, event: KeyEvent, index: int, count: int) -> int:
        """Return the new selected item after an up or down key."""
        if event.name in ("up", "w"):
            return (index - 1) % count
        if event.name in ("down", "s"):
            return (index + 1) % count
        return index

    def _key_menu(self, event: KeyEvent) -> None:
        """Keys of the main menu."""
        self.error = ""
        self.notice = ""
        self.menu_index = self._move_selection(event, self.menu_index,
                                               len(MENU_ITEMS))
        if event.name not in ("enter", "space"):
            return
        if self.menu_index == 0:
            self._start_game()
        elif self.menu_index == 1:
            self.scene = Scene.HIGHSCORES
        elif self.menu_index == 2:
            self.scene = Scene.INSTRUCTIONS
        else:
            self.running = False

    def _key_game(self, event: KeyEvent) -> None:
        """Keys while playing, or in the pause menu."""
        game = self.game
        if game is None:
            return
        if game.paused:
            self._key_pause(event, game)
            return
        if event.name in ("escape", "p"):
            self.pause_index = 0
            game.toggle_pause()
        elif event.name in DIRECTION_KEYS:
            game.set_direction(DIRECTION_KEYS[event.name])
        elif event.name == "c":
            game.toggle_cheat_mode()
        elif game.cheat_mode:
            self._key_cheat(event.name, game)

    def _key_pause(self, event: KeyEvent, game: Game) -> None:
        """Keys of the pause menu."""
        if event.name in ("escape", "p"):
            game.toggle_pause()
            return
        self.pause_index = self._move_selection(event, self.pause_index,
                                                len(PAUSE_ITEMS))
        if event.name in ("enter", "space"):
            if self.pause_index == 0:
                game.toggle_pause()
            else:
                self._to_menu()

    def _key_cheat(self, name: str, game: Game) -> None:
        """Keys of the cheat mode."""
        if name == "1":
            game.cheat_toggle_invincible()
        elif name == "2":
            game.cheat_toggle_freeze()
        elif name == "3":
            game.cheat_toggle_speed()
        elif name == "4":
            game.cheat_extra_life()
        elif name == "5":
            try:
                events = game.cheat_skip_level()
            except MazeError as error:
                self._abort_game(f"The game stopped: {error}")
                return
            self._after_events(events)
        elif name == "6":
            game.cheat_frighten_ghosts()

    def _after_events(self, events: list[GameEvent]) -> None:
        """Show the message of events that did not come from update()."""
        for event in events:
            if event in BANNERS:
                self.banner = BANNERS[event]
        if self.game is not None and self.game.state != GameState.PLAYING:
            self._finish_game(self.game)

    def _key_name(self, event: KeyEvent) -> None:
        """Keys of the screen where the player types a name."""
        if event.name == "enter":
            self._save_score()
        elif event.name == "escape":
            self.notice = "Score not saved"
            self._to_menu()
        elif event.name == "backspace":
            self.name_text = self.name_text[:-1]
        elif (event.char and is_valid_char(event.char)
                and len(self.name_text) < MAX_NAME_LENGTH):
            self.name_text += event.char

    # ----- changes of scene -----

    def _to_menu(self) -> None:
        """Go back to the main menu, dropping the current game."""
        self.scene = Scene.MENU
        self.game = None
        self.view = None
        self.banner = ""

    def _start_game(self) -> None:
        """Start a new game, or show why it is not possible."""
        try:
            self.game = Game(self.config)
        except MazeError as error:
            self.game = None
            self.error = f"Cannot start the game: {error}"
            return
        self.view = GameView(self.renderer, self.game)
        self.banner = ""
        self.scene = Scene.GAME

    def _abort_game(self, message: str) -> None:
        """Leave the game because something went wrong."""
        logger.error(message)
        self._to_menu()
        self.error = message

    def _finish_game(self, game: Game) -> None:
        """The game is over (lost or won): ask for the name."""
        self.final_score = game.score
        won = game.state == GameState.VICTORY
        self.end_title = "VICTORY!" if won else "GAME OVER"
        self.name_text = ""
        self.scene = Scene.NAME_ENTRY

    def _save_score(self) -> None:
        """Add the score to the highscores and go back to the menu."""
        position = self.highscores.add(self.name_text, self.final_score)
        saved = self.highscores.save()
        if position is None:
            self.notice = "Your score did not reach the top 10"
        else:
            self.notice = f"New highscore: position {position}!"
        if not saved:
            self.error = "The highscores could not be saved to the file"
        self._to_menu()

    # ----- drawing -----

    def draw(self, now: float) -> None:
        """Draw the current scene."""
        if self.scene == Scene.GAME and self.game and self.view:
            self.view.draw(self.game, now, self.banner)
            if self.game.paused:
                self._draw_pause()
            return
        self.renderer.clear(BACKGROUND)
        if self.scene == Scene.MENU:
            self._draw_menu()
        elif self.scene == Scene.HIGHSCORES:
            self._draw_highscores()
        elif self.scene == Scene.INSTRUCTIONS:
            self._draw_instructions()
        elif self.scene == Scene.NAME_ENTRY:
            self._draw_name_entry(now)

    def _draw_title(self, text: str, y: int = 50) -> None:
        """Draw a big yellow title."""
        self.renderer.draw_text(text, CENTER, y, 110, YELLOW, True)

    def _draw_items(self, items: tuple[str, ...], selected: int, y: int,
                    size: int = 48) -> None:
        """Draw a list of options, the selected one highlighted."""
        for index, item in enumerate(items):
            color = YELLOW if index == selected else TEXT
            label = f"> {item} <" if index == selected else item
            self.renderer.draw_text(label, CENTER, y + index * (size + 14),
                                    size, color, True)

    def _draw_scores(self, count: int, y: int, size: int) -> None:
        """Draw the first scores of the table."""
        entries = self.highscores.entries[:count]
        if not entries:
            self.renderer.draw_text("No scores yet", CENTER, y, size, GREY,
                                    True)
        for index, entry in enumerate(entries):
            text = f"{index + 1}. {entry.name} - {entry.score} pts"
            self.renderer.draw_text(text, CENTER, y + index * (size + 6),
                                    size, TEXT, True)

    def _draw_menu(self) -> None:
        """Main menu with the best scores underneath."""
        self._draw_title("Pac-Man")
        self._draw_items(MENU_ITEMS, self.menu_index, 190)
        self.renderer.draw_text("Highscores", CENTER, 460, 36, YELLOW, True)
        self._draw_scores(5, 500, 30)
        self._draw_messages()
        self.renderer.draw_text("UP / DOWN to choose, ENTER to select",
                                CENTER, WINDOW_HEIGHT - 30, 24, GREY, True)

    def _draw_messages(self) -> None:
        """Draw the error and the notice, if any."""
        if self.error:
            self.renderer.draw_text(self.error, CENTER, WINDOW_HEIGHT - 80,
                                    28, RED, True)
        if self.notice:
            self.renderer.draw_text(self.notice, CENTER, WINDOW_HEIGHT - 55,
                                    28, GREEN, True)

    def _draw_highscores(self) -> None:
        """The full top 10."""
        self._draw_title("Highscores", 40)
        self._draw_scores(MAX_ENTRIES, 190, 42)
        self.renderer.draw_text("Press ESC or ENTER to go back", CENTER,
                                WINDOW_HEIGHT - 40, 28, GREY, True)

    def _draw_instructions(self) -> None:
        """Controls and rules."""
        self._draw_title("Instructions", 40)
        for index, (line, color) in enumerate(INSTRUCTIONS):
            self.renderer.draw_text(line, CENTER, 190 + index * 38, 34,
                                    color, True)
        self.renderer.draw_text("Press ESC or ENTER to go back", CENTER,
                                WINDOW_HEIGHT - 40, 28, GREY, True)

    def _draw_pause(self) -> None:
        """Pause menu over the game."""
        width, height = 460, 300
        left = (WINDOW_WIDTH - width) // 2
        top = (WINDOW_HEIGHT - height) // 2 - 30
        draw_panel(self.renderer, left, top, width, height)
        self.renderer.draw_text("PAUSED", CENTER, top + 30, 72, YELLOW, True)
        self._draw_items(PAUSE_ITEMS, self.pause_index, top + 140, 40)

    def _draw_name_entry(self, now: float) -> None:
        """Game over or victory screen asking for the name."""
        won = self.end_title == "VICTORY!"
        self._draw_title(self.end_title, 70)
        if won:
            self.renderer.draw_text("Congratulations! You finished every "
                                    "level!", CENTER, 200, 34, GREEN, True)
        self.renderer.draw_text(f"Final score: {self.final_score}", CENTER,
                                270, 56, TEXT, True)
        self.renderer.draw_text("Enter your name:", CENTER, 380, 40, GREY,
                                True)
        cursor = "_" if int(now * 2) % 2 == 0 else " "
        draw_panel(self.renderer, CENTER - 230, 440, 460, 70)
        self.renderer.draw_text(self.name_text + cursor, CENTER, 455, 56,
                                YELLOW, True)
        self.renderer.draw_text("Up to 10 letters, numbers or spaces",
                                CENTER, 540, 26, GREY, True)
        self.renderer.draw_text("ENTER to save - ESC to skip", CENTER, 580,
                                30, TEXT, True)
