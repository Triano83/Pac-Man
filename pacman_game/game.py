"""Game rules: levels, player, ghosts, pellets, score, lives and time."""
import random
from enum import Enum

from pacman_game.config import GameConfig
from pacman_game.entities import (GHOST_NAMES, Direction, Ghost, GhostState,
                                  Player)
from pacman_game.ghost_ai import choose_next_cell
from pacman_game.maze import Maze, MazeError, generate_maze

READY_TIME = 2.0
FRIGHTENED_TIME = 8.0
RESPAWN_TIME = 5.0
PLAYER_INTERVAL = 0.15
FAST_PLAYER_INTERVAL = 0.07
GHOST_BASE_INTERVAL = 0.22
GHOST_MIN_INTERVAL = 0.16
GHOST_LEVEL_SPEEDUP = 0.005
FRIGHTENED_INTERVAL = 0.3
MAX_DT = 0.1
MAZE_RETRIES = 3


class GameState(Enum):
    """Global state of a game."""

    PLAYING = "playing"
    GAME_OVER = "game over"
    VICTORY = "victory"


class GameEvent(Enum):
    """Things that happen during update(); useful for sounds or messages."""

    PACGUM_EATEN = "pacgum eaten"
    SUPER_PACGUM_EATEN = "super pacgum eaten"
    GHOST_EATEN = "ghost eaten"
    LIFE_LOST = "life lost"
    TIME_UP = "time up"
    LEVEL_COMPLETE = "level complete"
    GAME_OVER = "game over"
    VICTORY = "victory"


def _build_maze(width: int, height: int, seed: int) -> Maze:
    """Generate a maze, retrying when a random one fails."""
    attempts = 1 if seed else MAZE_RETRIES
    error = MazeError("no attempt made")
    for _ in range(attempts):
        try:
            return generate_maze(width, height, seed)
        except MazeError as caught:
            error = caught
    raise error


class Game:
    """A whole game: from the first level to the victory or game over."""

    def __init__(self, config: GameConfig,
                 rng: random.Random | None = None) -> None:
        """Start a new game at level 1.

        Raises:
            MazeError: If the first maze cannot be generated.
        """
        self.config = config
        self.rng = rng if rng is not None else random.Random()
        self.score = 0
        self.lives = config.lives
        self.level_index = 0
        self.state = GameState.PLAYING
        self.paused = False
        self.cheat_mode = False
        self.invincible = False
        self.ghosts_frozen = False
        self.fast_player = False
        # Level data: created by _start_level().
        self.maze: Maze
        self.player_start: tuple[int, int]
        self.player: Player
        self.ghosts: list[Ghost]
        self.pacgums: set[tuple[int, int]]
        self.super_pacgums: set[tuple[int, int]]
        self.time_left: float
        self.frightened_timer: float
        self.ready_timer: float
        self._start_level()

    # ----- information for the screen -----

    @property
    def level_number(self) -> int:
        """Current level, starting at 1."""
        return self.level_index + 1

    @property
    def total_levels(self) -> int:
        """Number of levels of the game."""
        return len(self.config.levels)

    def player_progress(self) -> float:
        """Fraction (0 to 1) of the way from the previous cell to this one."""
        return min(1.0, self.player.timer / self._player_interval())

    def ghost_progress(self, ghost: Ghost) -> float:
        """Same as player_progress() for a ghost."""
        return min(1.0, ghost.timer / self._ghost_interval(ghost))

    # ----- actions of the user -----

    def set_direction(self, direction: Direction) -> None:
        """Remember the direction the player wants to take."""
        self.player.wanted = direction

    def toggle_pause(self) -> None:
        """Pause or resume the game."""
        if self.state == GameState.PLAYING:
            self.paused = not self.paused

    # ----- cheat mode -----

    def toggle_cheat_mode(self) -> bool:
        """Turn the cheat mode on or off; return the new value."""
        self.cheat_mode = not self.cheat_mode
        if not self.cheat_mode:
            self.invincible = False
            self.ghosts_frozen = False
            self.fast_player = False
        return self.cheat_mode

    def _cheats_allowed(self) -> bool:
        """Cheats work only if the cheat mode is on and the game goes on."""
        return self.cheat_mode and self.state == GameState.PLAYING

    def cheat_toggle_invincible(self) -> None:
        """Ghosts cannot hurt the player."""
        if self._cheats_allowed():
            self.invincible = not self.invincible

    def cheat_toggle_freeze(self) -> None:
        """Ghosts stop moving."""
        if self._cheats_allowed():
            self.ghosts_frozen = not self.ghosts_frozen

    def cheat_toggle_speed(self) -> None:
        """The player moves faster."""
        if self._cheats_allowed():
            self.fast_player = not self.fast_player

    def cheat_extra_life(self) -> None:
        """Add one life."""
        if self._cheats_allowed():
            self.lives += 1

    def cheat_frighten_ghosts(self) -> None:
        """Make the ghosts edible without eating a super-pacgum."""
        if self._cheats_allowed():
            self._frighten_ghosts()

    def cheat_skip_level(self) -> list[GameEvent]:
        """Win the current level at once."""
        events: list[GameEvent] = []
        if self._cheats_allowed():
            self._complete_level(events)
        return events

    # ----- main update -----

    def update(self, dt: float) -> list[GameEvent]:
        """Advance the game dt seconds and return what happened."""
        events: list[GameEvent] = []
        if self.state != GameState.PLAYING or self.paused:
            return events
        dt = min(dt, MAX_DT)
        if self.ready_timer > 0:
            self.ready_timer = max(0.0, self.ready_timer - dt)
            return events
        self._tick_timers(dt, events)
        if self._interrupted():
            return events
        self._move_player(dt, events)
        if self._interrupted():
            return events
        self._move_ghosts(dt, events)
        return events

    # ----- internal: levels -----

    def _start_level(self) -> None:
        """Build the maze, the pellets and the characters of a level."""
        level = self.config.levels[self.level_index]
        seed = self.config.seed if self.level_index == 0 else 0
        self.maze = _build_maze(level.width, level.height, seed)
        corners = self.maze.corners()
        self.player_start = self.maze.center_cell()
        self.player = Player(*self.player_start)
        self.ghosts = [Ghost(x, y, name=name)
                       for (x, y), name in zip(corners, GHOST_NAMES)]
        self.super_pacgums = set(corners)
        reserved = set(corners) | {self.player_start}
        self.pacgums = {cell for cell in self.maze.free_cells()
                        if cell not in reserved}
        self.time_left = float(self.config.level_max_time)
        self.frightened_timer = 0.0
        self.ready_timer = READY_TIME

    def _complete_level(self, events: list[GameEvent]) -> None:
        """Go to the next level, or win the game after the last one."""
        events.append(GameEvent.LEVEL_COMPLETE)
        if self.level_index + 1 >= self.total_levels:
            self.state = GameState.VICTORY
            events.append(GameEvent.VICTORY)
            return
        self.level_index += 1
        self._start_level()

    def _interrupted(self) -> bool:
        """True if the current frame must stop (death, new level, end)."""
        return self.state != GameState.PLAYING or self.ready_timer > 0

    # ----- internal: timers -----

    def _tick_timers(self, dt: float, events: list[GameEvent]) -> None:
        """Update the level clock, the frightened time and the respawns."""
        self.time_left -= dt
        if self.time_left <= 0:
            events.append(GameEvent.TIME_UP)
            self._lose_life(events, reset_clock=True)
            return
        if self.frightened_timer > 0:
            self.frightened_timer = max(0.0, self.frightened_timer - dt)
            if self.frightened_timer == 0:
                for ghost in self.ghosts:
                    if ghost.state == GhostState.FRIGHTENED:
                        ghost.state = GhostState.CHASING
        for ghost in self.ghosts:
            if ghost.state == GhostState.RESPAWNING:
                ghost.respawn_timer -= dt
                if ghost.respawn_timer <= 0:
                    ghost.respawn_timer = 0.0
                    ghost.state = GhostState.CHASING

    # ----- internal: player -----

    def _player_interval(self) -> float:
        """Seconds the player needs to cross one cell."""
        return FAST_PLAYER_INTERVAL if self.fast_player else PLAYER_INTERVAL

    def _move_player(self, dt: float, events: list[GameEvent]) -> None:
        """Move the player as many cells as the elapsed time allows."""
        player = self.player
        player.timer += dt
        interval = self._player_interval()
        while player.timer >= interval:
            player.timer -= interval
            self._step_player(events)
            if self._interrupted():
                return

    def _step_player(self, events: list[GameEvent]) -> None:
        """Move the player one cell (if there is no wall) and eat."""
        player = self.player
        wanted = player.wanted
        if wanted != Direction.NONE and self.maze.can_move(
                player.x, player.y, wanted.wall_bit):
            player.direction = wanted
        direction = player.direction
        if direction == Direction.NONE or not self.maze.can_move(
                player.x, player.y, direction.wall_bit):
            player.direction = Direction.NONE
            player.prev_x, player.prev_y = player.x, player.y
            return
        player.move_to(player.x + direction.dx, player.y + direction.dy)
        self._eat_pellets(events)
        if not self.pacgums and not self.super_pacgums:
            self._complete_level(events)
            return
        self._check_collisions(events)

    def _eat_pellets(self, events: list[GameEvent]) -> None:
        """Eat the pellet of the player's cell, if any."""
        cell = self.player.cell
        if cell in self.pacgums:
            self.pacgums.remove(cell)
            self.score += self.config.points_per_pacgum
            events.append(GameEvent.PACGUM_EATEN)
        elif cell in self.super_pacgums:
            self.super_pacgums.remove(cell)
            self.score += self.config.points_per_super_pacgum
            events.append(GameEvent.SUPER_PACGUM_EATEN)
            self._frighten_ghosts()

    # ----- internal: ghosts -----

    def _frighten_ghosts(self) -> None:
        """Make every active ghost edible for a while."""
        self.frightened_timer = FRIGHTENED_TIME
        for ghost in self.ghosts:
            if ghost.state == GhostState.CHASING:
                ghost.state = GhostState.FRIGHTENED

    def _ghost_interval(self, ghost: Ghost) -> float:
        """Seconds a ghost needs to cross one cell."""
        if ghost.state == GhostState.FRIGHTENED:
            return FRIGHTENED_INTERVAL
        speedup = GHOST_LEVEL_SPEEDUP * self.level_index
        return max(GHOST_MIN_INTERVAL, GHOST_BASE_INTERVAL - speedup)

    def _move_ghosts(self, dt: float, events: list[GameEvent]) -> None:
        """Move every ghost as many cells as the elapsed time allows."""
        if self.ghosts_frozen:
            return
        for ghost in self.ghosts:
            if ghost.state == GhostState.RESPAWNING:
                continue
            ghost.timer += dt
            interval = self._ghost_interval(ghost)
            while ghost.timer >= interval:
                ghost.timer -= interval
                x, y = choose_next_cell(self.maze, ghost, self.player,
                                        self.rng)
                ghost.move_to(x, y)
                self._check_collisions(events)
                if self._interrupted():
                    return
                if ghost.state == GhostState.RESPAWNING:
                    break

    def _check_collisions(self, events: list[GameEvent]) -> None:
        """Handle a ghost and the player being in the same cell."""
        for ghost in self.ghosts:
            if (ghost.state == GhostState.RESPAWNING
                    or ghost.cell != self.player.cell):
                continue
            if ghost.state == GhostState.FRIGHTENED:
                self.score += self.config.points_per_ghost
                events.append(GameEvent.GHOST_EATEN)
                ghost.place(*ghost.home)
                ghost.state = GhostState.RESPAWNING
                ghost.respawn_timer = RESPAWN_TIME
            elif not self.invincible:
                self._lose_life(events, reset_clock=False)
                return

    # ----- internal: lives -----

    def _lose_life(self, events: list[GameEvent], reset_clock: bool) -> None:
        """Take one life; end the game or put everybody back at the start."""
        self.lives -= 1
        events.append(GameEvent.LIFE_LOST)
        if self.lives <= 0:
            self.lives = 0
            self.state = GameState.GAME_OVER
            events.append(GameEvent.GAME_OVER)
            return
        self.player.place(*self.player_start)
        self.player.direction = Direction.NONE
        self.player.wanted = Direction.NONE
        for ghost in self.ghosts:
            ghost.place(*ghost.home)
            ghost.state = GhostState.CHASING
            ghost.respawn_timer = 0.0
        self.frightened_timer = 0.0
        self.ready_timer = READY_TIME
        if reset_clock:
            self.time_left = float(self.config.level_max_time)
