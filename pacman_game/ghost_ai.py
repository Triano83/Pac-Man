"""Decides where a ghost goes next: every ghost has its own personality."""
import random

from pacman_game.entities import Direction, Ghost, GhostState, Player
from pacman_game.maze import Maze

AHEAD_STEPS = 4
CLYDE_SAFE_DISTANCE = 8
INKY_CHASE_PROBABILITY = 0.5


def ahead_cell(maze: Maze, player: Player,
               steps: int = AHEAD_STEPS) -> tuple[int, int]:
    """Return the cell the player will reach going straight on.

    The walk stops at a wall or after the given number of steps.
    """
    x, y = player.cell
    direction = player.direction
    if direction == Direction.NONE:
        return x, y
    for _ in range(steps):
        if not maze.can_move(x, y, direction.wall_bit):
            break
        x, y = x + direction.dx, y + direction.dy
    return x, y


def _target(maze: Maze, ghost: Ghost, player: Player,
            rng: random.Random) -> tuple[int, int] | None:
    """Return the cell the ghost wants to reach, or None to wander."""
    if ghost.name == "Pinky":
        return ahead_cell(maze, player)
    if ghost.name == "Inky":
        return player.cell if rng.random() < INKY_CHASE_PROBABILITY else None
    if ghost.name == "Clyde":
        gap = (abs(ghost.x - player.x) + abs(ghost.y - player.y))
        return player.cell if gap > CLYDE_SAFE_DISTANCE else ghost.home
    return player.cell


def choose_next_cell(maze: Maze, ghost: Ghost, player: Player,
                     rng: random.Random) -> tuple[int, int]:
    """Return the neighbor cell the ghost moves to.

    Blinky chases the player, Pinky heads for the cell ahead of the player,
    Inky chases or wanders at random and Clyde chases from far away but
    runs back to his corner when he gets close. Frightened ghosts run away.
    Ghosts never turn back unless they are in a dead end.
    """
    options = maze.neighbors(ghost.x, ghost.y)
    if not options:
        return ghost.cell
    back = (ghost.prev_x, ghost.prev_y)
    if len(options) > 1 and back in options:
        options.remove(back)
    if len(options) == 1:
        return options[0]
    rng.shuffle(options)
    if ghost.state == GhostState.FRIGHTENED:
        away = maze.distances_from(*player.cell)
        return max(options, key=lambda cell: away.get(cell, 0))
    target = _target(maze, ghost, player, rng)
    if target is None:
        return options[0]
    toward = maze.distances_from(*target)
    return min(options, key=lambda cell: toward.get(cell, 10**6))
