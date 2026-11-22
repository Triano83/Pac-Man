"""Basic objects of the game: directions, the player and the ghosts."""
from dataclasses import dataclass, field
from enum import Enum

from pacman_game.maze import EAST, NORTH, SOUTH, WEST

GHOST_NAMES = ("Blinky", "Pinky", "Inky", "Clyde")


class Direction(Enum):
    """The four directions of movement, plus NONE (standing still)."""

    NONE = (0, 0, 0)
    UP = (0, -1, NORTH)
    DOWN = (0, 1, SOUTH)
    LEFT = (-1, 0, WEST)
    RIGHT = (1, 0, EAST)

    def __init__(self, dx: int, dy: int, wall_bit: int) -> None:
        """Store the step on each axis and the wall bit of that side."""
        self.dx = dx
        self.dy = dy
        self.wall_bit = wall_bit


class GhostState(Enum):
    """What a ghost is doing at a given moment."""

    CHASING = "chasing"
    FRIGHTENED = "frightened"
    RESPAWNING = "respawning"


@dataclass
class Actor:
    """Something that lives in a maze cell and moves from cell to cell.

    The previous cell and the timer are kept so that the screen can draw
    a smooth movement between two cells.
    """

    x: int
    y: int
    prev_x: int = field(init=False)
    prev_y: int = field(init=False)
    timer: float = 0.0

    def __post_init__(self) -> None:
        """At the start the previous cell is the current one."""
        self.prev_x = self.x
        self.prev_y = self.y

    @property
    def cell(self) -> tuple[int, int]:
        """Return the current cell as (x, y)."""
        return self.x, self.y

    def place(self, x: int, y: int) -> None:
        """Put the actor in a cell at once (no movement)."""
        self.x = self.prev_x = x
        self.y = self.prev_y = y
        self.timer = 0.0

    def move_to(self, x: int, y: int) -> None:
        """Move the actor to a neighbor cell, remembering where it was."""
        self.prev_x, self.prev_y = self.x, self.y
        self.x, self.y = x, y


@dataclass
class Player(Actor):
    """The Pac-Man controlled by the user."""

    direction: Direction = Direction.NONE
    wanted: Direction = Direction.NONE


@dataclass
class Ghost(Actor):
    """One of the four ghosts."""

    name: str = ""
    state: GhostState = GhostState.CHASING
    respawn_timer: float = 0.0
    home: tuple[int, int] = field(init=False)

    def __post_init__(self) -> None:
        """The cell where the ghost is created is its home corner."""
        super().__post_init__()
        self.home = (self.x, self.y)
