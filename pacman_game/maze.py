"""Adapter between the assigned A-Maze-ing package and the game."""
from collections import deque
from dataclasses import dataclass

# Wall bits used by the generator: a bit set to 1 means "there is a wall".
NORTH = 1
EAST = 2
SOUTH = 4
WEST = 8
# (wall bit, dx, dy) for each of the four directions.
MOVES: tuple[tuple[int, int, int], ...] = (
    (NORTH, 0, -1),
    (EAST, 1, 0),
    (SOUTH, 0, 1),
    (WEST, -1, 0),
)
# A cell with the four walls closed: part of the '42' drawing.
SOLID = 15
# The game needs mazes with loops (no dead ends), so never perfect.
PERFECT = False


class MazeError(Exception):
    """Raised when the maze cannot be generated or is not usable."""


@dataclass
class Maze:
    """A maze as a grid of wall bitmasks, indexed as cells[y][x]."""

    width: int
    height: int
    cells: list[list[int]]

    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if (x, y) is inside the grid."""
        return 0 <= x < self.width and 0 <= y < self.height

    def is_solid(self, x: int, y: int) -> bool:
        """Return True if the cell belongs to the '42' drawing."""
        return self.cells[y][x] == SOLID

    def can_move(self, x: int, y: int, wall_bit: int) -> bool:
        """Return True if one can leave (x, y) through the given side."""
        if self.cells[y][x] & wall_bit:
            return False
        for bit, dx, dy in MOVES:
            if bit == wall_bit:
                nx, ny = x + dx, y + dy
                return self.in_bounds(nx, ny) and not self.is_solid(nx, ny)
        return False

    def neighbors(self, x: int, y: int) -> list[tuple[int, int]]:
        """Return the cells reachable in one step from (x, y)."""
        result = []
        for bit, dx, dy in MOVES:
            if self.can_move(x, y, bit):
                result.append((x + dx, y + dy))
        return result

    def distances_from(self, x: int, y: int) -> dict[tuple[int, int], int]:
        """Return the walking distance from (x, y) to every reachable cell."""
        distances = {(x, y): 0}
        queue = deque([(x, y)])
        while queue:
            cx, cy = queue.popleft()
            for neighbor in self.neighbors(cx, cy):
                if neighbor not in distances:
                    distances[neighbor] = distances[(cx, cy)] + 1
                    queue.append(neighbor)
        return distances

    def free_cells(self) -> list[tuple[int, int]]:
        """Return every cell that is not part of the '42' drawing."""
        return [(x, y) for y in range(self.height)
                for x in range(self.width) if not self.is_solid(x, y)]

    def corners(self) -> list[tuple[int, int]]:
        """Return the 4 corners: TL, TR, BL, BR."""
        right, bottom = self.width - 1, self.height - 1
        return [(0, 0), (right, 0), (0, bottom), (right, bottom)]

    def center_cell(self) -> tuple[int, int]:
        """Return the free cell closest to the middle of the maze."""
        cx, cy = self.width // 2, self.height // 2
        return min(self.free_cells(),
                   key=lambda cell: abs(cell[0] - cx) + abs(cell[1] - cy))

    def to_ascii(self) -> str:
        """Draw the maze with text characters (useful for debugging)."""
        lines = []
        for y in range(self.height):
            top = bottom = ""
            for x in range(self.width):
                cell = self.cells[y][x]
                top += "+" + ("--" if cell & NORTH else "  ")
                side = "##" if cell == SOLID else "  "
                bottom += ("|" if cell & WEST else " ") + side
            lines.append(top + "+")
            lines.append(bottom + ("|" if self.cells[y][-1] & EAST else " "))
        lines.append("+" + ("--+" * self.width))
        return "\n".join(lines)


def _validate(raw: object, width: int, height: int) -> list[list[int]]:
    """Check the data given by the generator and return a clean copy."""
    if not isinstance(raw, list) or len(raw) != height:
        raise MazeError("The generator returned a maze with a wrong height")
    cells: list[list[int]] = []
    for row in raw:
        if not isinstance(row, list) or len(row) != width:
            raise MazeError("The generator returned a maze with a wrong width")
        for value in row:
            if (isinstance(value, bool) or not isinstance(value, int)
                    or not 0 <= value <= SOLID):
                raise MazeError("The generator returned an invalid cell")
        cells.append([int(value) for value in row])
    return cells


def _check_connected(maze: Maze) -> None:
    """Raise MazeError if some free cells cannot be reached from others."""
    free = maze.free_cells()
    if not free:
        raise MazeError("The generated maze has no free cells")
    seen = {free[0]}
    queue = deque([free[0]])
    while queue:
        x, y = queue.popleft()
        for neighbor in maze.neighbors(x, y):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    if len(seen) != len(free):
        raise MazeError("The generated maze is not fully connected")


def generate_maze(width: int, height: int, seed: int = 0) -> Maze:
    """Generate a maze with the assigned A-Maze-ing package.

    Args:
        width: Number of columns.
        height: Number of rows.
        seed: Fixed seed (>= 1) for a reproducible maze, 0 for a random one.

    Returns:
        The generated maze.

    Raises:
        MazeError: If the package is missing, fails or returns bad data.
    """
    try:
        from mazegenerator import MazeGenerator
    except ImportError as error:
        raise MazeError("Package 'mazegenerator' is not installed "
                        "(run 'make install')") from error
    try:
        generator = MazeGenerator(size=(width, height), perfect=PERFECT,
                                  seed=seed)
        raw = generator.maze
    except Exception as error:  # third-party code: we cannot predict errors
        raise MazeError(f"The maze generator failed: {error}") from error
    maze = Maze(width, height, _validate(raw, width, height))
    _check_connected(maze)
    return maze
