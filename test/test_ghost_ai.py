"""Tests for the personality of the ghosts."""
import random

from pacman_game.config import GameConfig
from pacman_game.entities import Direction, Ghost, GhostState, Player
from pacman_game.ghost_ai import ahead_cell, choose_next_cell
from pacman_game.maze import Maze, generate_maze


def make_maze() -> Maze:
    """Return the maze of the first level."""
    config = GameConfig()
    return generate_maze(config.levels[0].width, config.levels[0].height,
                         config.seed)


def make_ghost(maze: Maze, name: str, corner: int = 0) -> Ghost:
    """Return a ghost standing in one corner of the maze."""
    x, y = maze.corners()[corner]
    return Ghost(x, y, name=name)


def walk(maze: Maze, ghost: Ghost, player: Player, steps: int,
         rng: random.Random) -> list[int]:
    """Move the ghost step by step; return its distance to the player."""
    distances = []
    for _ in range(steps):
        ghost.move_to(*choose_next_cell(maze, ghost, player, rng))
        distances.append(maze.distances_from(*player.cell)[ghost.cell])
    return distances


def test_distances_from() -> None:
    """Distances cover every free cell and grow by one per step."""
    maze = make_maze()
    start = maze.center_cell()
    distances = maze.distances_from(*start)
    assert distances[start] == 0
    assert set(distances) == set(maze.free_cells())
    for cell, distance in distances.items():
        for neighbor in maze.neighbors(*cell):
            assert abs(distances[neighbor] - distance) == 1


def test_blinky_goes_straight_to_the_player() -> None:
    """Blinky follows a shortest path: one cell closer at every step."""
    maze = make_maze()
    player = Player(*maze.center_cell())
    ghost = make_ghost(maze, "Blinky")
    first = maze.distances_from(*player.cell)[ghost.cell]
    distances = walk(maze, ghost, player, first, random.Random(1))
    assert distances == list(range(first - 1, -1, -1))
    assert ghost.cell == player.cell


def test_pinky_aims_ahead_of_the_player() -> None:
    """Pinky heads for the cell the player is about to reach."""
    maze = make_maze()
    player = Player(*maze.center_cell())
    assert ahead_cell(maze, player) == player.cell
    for direction in (Direction.UP, Direction.DOWN,
                      Direction.LEFT, Direction.RIGHT):
        player.direction = direction
        cell = ahead_cell(maze, player)
        distance = maze.distances_from(*player.cell)[cell]
        assert distance <= 4
        assert (cell[0] - player.x) * direction.dx >= 0
        assert (cell[1] - player.y) * direction.dy >= 0
    player.direction = Direction.RIGHT
    ghost = make_ghost(maze, "Pinky", corner=3)
    target = ahead_cell(maze, player)
    first = maze.distances_from(*target)[ghost.cell]
    distances = []
    for _ in range(first):
        ghost.move_to(*choose_next_cell(maze, ghost, player,
                                        random.Random(1)))
        distances.append(maze.distances_from(*target)[ghost.cell])
    assert distances == list(range(first - 1, -1, -1))


def test_clyde_chases_from_far_and_retreats_when_close() -> None:
    """Clyde comes closer when far, but goes home when near the player."""
    maze = make_maze()
    player = Player(*maze.center_cell())
    far = make_ghost(maze, "Clyde", corner=0)
    assert abs(far.x - player.x) + abs(far.y - player.y) > 8
    before = maze.distances_from(*player.cell)[far.cell]
    far.move_to(*choose_next_cell(maze, far, player, random.Random(1)))
    assert maze.distances_from(*player.cell)[far.cell] == before - 1
    near = make_ghost(maze, "Clyde", corner=0)
    home = maze.distances_from(*near.home)
    for cell in maze.free_cells():
        gap = abs(cell[0] - player.x) + abs(cell[1] - player.y)
        if gap <= 8 and home[cell] > 3:
            near.place(*cell)
            break
    before = home[near.cell]
    near.move_to(*choose_next_cell(maze, near, player, random.Random(1)))
    assert home[near.cell] == before - 1


def test_inky_sometimes_chases_and_sometimes_wanders() -> None:
    """Inky is unpredictable: some steps get closer, some do not."""
    maze = make_maze()
    player = Player(*maze.center_cell())
    ghost = make_ghost(maze, "Inky")
    rng = random.Random(3)
    closer = farther = 0
    for _ in range(300):
        before = maze.distances_from(*player.cell)[ghost.cell]
        ghost.move_to(*choose_next_cell(maze, ghost, player, rng))
        after = maze.distances_from(*player.cell)[ghost.cell]
        closer += after < before
        farther += after > before
    assert closer > 30 and farther > 30


def test_frightened_ghost_runs_away() -> None:
    """A frightened ghost ends up farther from the player than it began."""
    maze = make_maze()
    player = Player(*maze.center_cell())
    for name in ("Blinky", "Pinky", "Inky", "Clyde"):
        ghost = make_ghost(maze, name)
        start = maze.neighbors(*player.cell)[0]
        ghost.place(*start)
        ghost.state = GhostState.FRIGHTENED
        distances = walk(maze, ghost, player, 12, random.Random(5))
        assert distances[-1] > 1
        assert max(distances) >= 8


def test_ghosts_only_turn_back_in_dead_ends() -> None:
    """With two or more options a ghost never goes back."""
    maze = make_maze()
    player = Player(*maze.center_cell())
    rng = random.Random(9)
    for name in ("Blinky", "Pinky", "Inky", "Clyde"):
        ghost = make_ghost(maze, name)
        for _ in range(200):
            options = maze.neighbors(*ghost.cell)
            back = (ghost.prev_x, ghost.prev_y)
            ghost.move_to(*choose_next_cell(maze, ghost, player, rng))
            if len(options) > 1:
                assert ghost.cell != back
            assert ghost.cell in options
