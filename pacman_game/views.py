"""Drawing of the game screen: maze, pellets, characters and HUD."""
import math

from pacman_game.entities import Actor, Direction, Ghost, GhostState
from pacman_game.game import Game, GameState
from pacman_game.maze import EAST, NORTH, SOUTH, WEST, Maze
from pacman_game.renderer import Color, Image, Renderer
from pacman_game.sprites import SpriteFactory

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 800
HUD_HEIGHT = 64
HUD_ICON_SIZE = 24
MIN_CELL = 6
MAX_CELL = 40
FLASH_TIME = 2.0

BACKGROUND: Color = (16, 16, 24)
WALL: Color = (70, 100, 255)
SOLID: Color = (45, 60, 170)
TEXT: Color = (255, 255, 255)
HUD_LINE: Color = (70, 70, 90)
CHEAT_ON: Color = (80, 255, 80)
CHEAT_OFF: Color = (150, 150, 150)
CHEAT_KEYS = (("1", "invincible"), ("2", "freeze"), ("3", "speed"),
              ("4", "+life"), ("5", "skip"), ("6", "edible"))
MOUTH_CYCLE = (0, 1, 2, 1)


def draw_panel(renderer: Renderer, x: int, y: int, width: int,
               height: int) -> None:
    """Draw a dark box with a border (used behind messages)."""
    renderer.fill_rect(x - 3, y - 3, width + 6, height + 6, WALL)
    renderer.fill_rect(x, y, width, height, BACKGROUND)


class GameView:
    """Draws a Game on the window."""

    def __init__(self, renderer: Renderer, game: Game) -> None:
        """Prepare the layout for the maze of the game."""
        self.renderer = renderer
        self.facing = Direction.RIGHT
        self._factories: dict[int, SpriteFactory] = {}
        self._hud_sprites = SpriteFactory(renderer, HUD_ICON_SIZE)
        self._layout(game)

    def _layout(self, game: Game) -> None:
        """Choose the cell size and build the picture of the walls."""
        maze = game.maze
        space = WINDOW_HEIGHT - HUD_HEIGHT
        cell = min(MAX_CELL, WINDOW_WIDTH // maze.width, space // maze.height)
        self.cell = max(MIN_CELL, cell)
        self.offset_x = (WINDOW_WIDTH - maze.width * self.cell) // 2
        self.offset_y = (space - maze.height * self.cell) // 2
        if self.cell not in self._factories:
            self._factories[self.cell] = SpriteFactory(self.renderer,
                                                       self.cell)
        self.sprites = self._factories[self.cell]
        self.maze_image = self._build_maze_image(maze)
        self._maze = maze

    def _build_maze_image(self, maze: Maze) -> Image:
        """Draw all the walls once, in a picture."""
        cell = self.cell
        thick = max(1, cell // 12)
        image = self.renderer.new_image(maze.width * cell, maze.height * cell)
        for y in range(maze.height):
            for x in range(maze.width):
                value = maze.cells[y][x]
                left, top = x * cell, y * cell
                if maze.is_solid(x, y):
                    image.fill_rect(left, top, cell, cell, SOLID)
                    continue
                if value & NORTH:
                    image.fill_rect(left, top, cell, thick, WALL)
                if value & SOUTH:
                    image.fill_rect(left, top + cell - thick, cell, thick,
                                    WALL)
                if value & WEST:
                    image.fill_rect(left, top, thick, cell, WALL)
                if value & EAST:
                    image.fill_rect(left + cell - thick, top, thick, cell,
                                    WALL)
        return image

    def _position(self, actor: Actor, progress: float) -> tuple[int, int]:
        """Pixel position of an actor, between its previous cell and now."""
        x = actor.prev_x + (actor.x - actor.prev_x) * progress
        y = actor.prev_y + (actor.y - actor.prev_y) * progress
        return (self.offset_x + round(x * self.cell),
                self.offset_y + round(y * self.cell))

    def draw(self, game: Game, now: float, banner: str = "") -> None:
        """Draw one complete frame of the game."""
        if game.maze is not self._maze:
            self._layout(game)
        renderer = self.renderer
        renderer.clear(BACKGROUND)
        renderer.put_image(self.maze_image, self.offset_x, self.offset_y)
        self._draw_pellets(game, now)
        self._draw_ghosts(game, now)
        self._draw_player(game, now)
        self._draw_hud(game)
        if game.ready_timer > 0 and game.state == GameState.PLAYING:
            self._draw_ready(game, banner)

    def _draw_pellets(self, game: Game, now: float) -> None:
        """Draw the pacgums and the (blinking) super-pacgums."""
        small = self.sprites.pacgum()
        for x, y in game.pacgums:
            self.renderer.put_image(small, self.offset_x + x * self.cell,
                                    self.offset_y + y * self.cell)
        if int(now * 4) % 2 == 0:
            big = self.sprites.super_pacgum()
            for x, y in game.super_pacgums:
                self.renderer.put_image(big, self.offset_x + x * self.cell,
                                        self.offset_y + y * self.cell)

    def _ghost_mode(self, game: Game, ghost: Ghost, now: float) -> str:
        """Choose how a ghost looks like at this moment."""
        if ghost.state == GhostState.RESPAWNING:
            return "eyes"
        if ghost.state == GhostState.FRIGHTENED:
            if game.frightened_timer < FLASH_TIME and int(now * 4) % 2 == 0:
                return "flash"
            return "scared"
        return "normal"

    def _draw_ghosts(self, game: Game, now: float) -> None:
        """Draw the four ghosts."""
        for ghost in game.ghosts:
            dx = ghost.x - ghost.prev_x
            dy = ghost.y - ghost.prev_y
            look = (max(-1, min(1, dx)), max(-1, min(1, dy)))
            mode = self._ghost_mode(game, ghost, now)
            image = self.sprites.ghost(ghost.name, mode, look)
            x, y = self._position(ghost, game.ghost_progress(ghost))
            self.renderer.put_image(image, x, y)

    def _draw_player(self, game: Game, now: float) -> None:
        """Draw Pac-Man, with the mouth opening and closing when moving."""
        player = game.player
        if player.direction != Direction.NONE:
            self.facing = player.direction
            mouth = MOUTH_CYCLE[int(now * 12) % len(MOUTH_CYCLE)]
        else:
            mouth = 1
        image = self.sprites.pacman(self.facing, mouth)
        x, y = self._position(player, game.player_progress())
        self.renderer.put_image(image, x, y)

    def _draw_hud(self, game: Game) -> None:
        """Draw score, lives, level and time, plus the cheat panel."""
        renderer = self.renderer
        top = WINDOW_HEIGHT - HUD_HEIGHT
        renderer.fill_rect(0, top, WINDOW_WIDTH, 2, HUD_LINE)
        renderer.draw_text(f"Score: {game.score}", 16, top + 10, 30, TEXT)
        renderer.draw_text("Lives:", 230, top + 10, 30, TEXT)
        icon = self._hud_sprites.pacman(Direction.RIGHT, 1)
        for index in range(min(game.lives, 8)):
            renderer.put_image(icon, 320 + index * (HUD_ICON_SIZE + 4),
                               top + 8)
        if game.lives > 8:
            renderer.draw_text(f"x{game.lives}", 320 + 8 * 28, top + 10,
                               26, TEXT)
        renderer.draw_text(f"Level: {game.level_number}/{game.total_levels}",
                           540, top + 10, 30, TEXT)
        seconds = max(0, math.ceil(game.time_left))
        renderer.draw_text(f"Time: {seconds}", 690, top + 10, 30, TEXT)
        if game.cheat_mode:
            self._draw_cheats(game, top + 40)

    def _draw_cheats(self, game: Game, y: int) -> None:
        """Draw the list of cheats and which of them are active."""
        renderer = self.renderer
        renderer.draw_text("CHEAT MODE:", 16, y, 22, (255, 120, 60))
        active = {"1": game.invincible, "2": game.ghosts_frozen,
                  "3": game.fast_player}
        x = 150
        for key, label in CHEAT_KEYS:
            color = CHEAT_ON if active.get(key, False) else CHEAT_OFF
            text = f"[{key}] {label}"
            renderer.draw_text(text, x, y, 22, color)
            x += renderer.text_width(text, 22) + 14

    def _draw_ready(self, game: Game, banner: str) -> None:
        """Draw the message shown before the player can move."""
        lines = [banner] if banner else []
        lines += [f"Level {game.level_number}", "Get ready!"]
        width, height = 420, 40 + 52 * len(lines)
        left = (WINDOW_WIDTH - width) // 2
        top = self.offset_y + 3 * self.cell
        draw_panel(self.renderer, left, top, width, height)
        for index, line in enumerate(lines):
            color = (255, 238, 0) if index == len(lines) - 1 else TEXT
            self.renderer.draw_text(line, WINDOW_WIDTH // 2,
                                    top + 22 + 52 * index, 48, color, True)
