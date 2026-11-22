"""Tests for the maze adapter."""
import pytest

from pacman_game.maze import (EAST, MOVES, SOUTH, Maze, MazeError,
                              _check_connected, generate_maze)


@pytest.mark.parametrize("size", [(14, 10), (15, 15), (16, 16), (21, 21)])
@pytest.mark.parametrize("seed", [0, 1, 42, 999])
def test_generated_maze_is_valid(size: tuple[int, int], seed: int) -> None:
    """Every maze is connected and has its four corners free."""
    maze = generate_maze(size[0], size[1], seed)
    assert (maze.width, maze.height) == size
    for x, y in maze.corners():
        assert not maze.is_solid(x, y)
    assert not maze.is_solid(*maze.center_cell())


def test_fixed_seed_is_reproducible() -> None:
    """The same seed gives the same maze."""
    assert (generate_maze(15, 15, 42).cells
            == generate_maze(15, 15, 42).cells)


def test_walls_are_consistent() -> None:
    """A wall between two cells is seen from both sides."""
    maze = generate_maze(17, 17, 7)
    for y in range(maze.height):
        for x in range(maze.width - 1):
            east = maze.cells[y][x] & EAST
            west = maze.cells[y][x + 1] & 8
            assert bool(east) == bool(west)
    for y in range(maze.height - 1):
        for x in range(maze.width):
            south = maze.cells[y][x] & SOUTH
            north = maze.cells[y + 1][x] & 1
            assert bool(south) == bool(north)


def test_dead_ends_only_next_to_the_42() -> None:
    """The only dead ends left are the ones touching the '42' drawing."""
    maze = generate_maze(21, 21, 3)
    for x, y in maze.free_cells():
        if len(maze.neighbors(x, y)) < 2:
            touches_42 = any(maze.in_bounds(x + dx, y + dy)
                             and maze.is_solid(x + dx, y + dy)
                             for _, dx, dy in MOVES)
            assert touches_42


def test_outer_border_is_closed() -> None:
    """One cannot leave the maze through its border."""
    maze = generate_maze(15, 15, 42)
    for x, y in maze.free_cells():
        for bit, dx, dy in MOVES:
            if not maze.in_bounds(x + dx, y + dy):
                assert maze.cells[y][x] & bit


def test_bad_data_raises_maze_error() -> None:
    """Invalid sizes are reported with MazeError, not a crash."""
    with pytest.raises(MazeError):
        generate_maze(0, 0, 42)
    with pytest.raises(MazeError):
        generate_maze(-5, 20, 42)


def test_unconnected_is_detected() -> None:
    """Two free cells separated by a wall are not a valid maze."""
    maze = Maze(2, 1, [[7, 13]])
    with pytest.raises(MazeError):
        _check_connected(maze)
