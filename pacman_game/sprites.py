"""Pictures of the game, drawn pixel by pixel when they are first needed."""
import math
from collections.abc import Callable

from pacman_game.entities import Direction
from pacman_game.renderer import Color, Image, Renderer

Shape = Callable[[float, float], Color | None]

YELLOW: Color = (255, 238, 0)
WHITE: Color = (255, 255, 255)
BLUE: Color = (33, 33, 255)
PELLET: Color = (255, 184, 174)
GHOST_COLORS: dict[str, Color] = {
    "Blinky": (255, 0, 0),
    "Pinky": (255, 184, 255),
    "Inky": (0, 255, 255),
    "Clyde": (255, 184, 82),
}
FACING_ANGLE = {Direction.RIGHT: 0.0, Direction.DOWN: 90.0,
                Direction.LEFT: 180.0, Direction.UP: 270.0,
                Direction.NONE: 0.0}
MOUTH_HALF_ANGLES = (0.0, 22.0, 45.0)
SUBSAMPLES = 2


def paint(renderer: Renderer, size: int, shape: Shape) -> Image:
    """Build an image by asking shape(u, v) for the color of each point.

    u and v go from -1 to 1 (v grows downwards). shape returns None for
    transparent points. Each pixel is sampled 4 times to smooth the edges.
    """
    image = renderer.new_image(size, size)
    total = SUBSAMPLES * SUBSAMPLES
    for py in range(size):
        for px in range(size):
            colors = []
            for sy in range(SUBSAMPLES):
                for sx in range(SUBSAMPLES):
                    u = (px + (sx + 0.5) / SUBSAMPLES) / size * 2 - 1
                    v = (py + (sy + 0.5) / SUBSAMPLES) / size * 2 - 1
                    color = shape(u, v)
                    if color is not None:
                        colors.append(color)
            if colors:
                count = len(colors)
                red = sum(c[0] for c in colors) // count
                green = sum(c[1] for c in colors) // count
                blue = sum(c[2] for c in colors) // count
                image.set_pixel(px, py, (red, green, blue,
                                         255 * count // total))
    return image


def pacman_shape(direction: Direction, half_angle: float) -> Shape:
    """Shape of Pac-Man looking to a direction with the mouth open."""
    facing = FACING_ANGLE[direction]

    def shape(u: float, v: float) -> Color | None:
        """Return the color of one point of Pac-Man."""
        if u * u + v * v > 0.85 ** 2:
            return None
        if half_angle > 0:
            angle = math.degrees(math.atan2(v, u))
            gap = abs((angle - facing + 180) % 360 - 180)
            if gap < half_angle:
                return None
        return YELLOW

    return shape


def ghost_shape(color: Color, mode: str, look: tuple[int, int]) -> Shape:
    """Shape of a ghost.

    mode is "normal", "scared", "flash" (scared, about to end) or "eyes".
    look is the direction (dx, dy) the eyes look to.
    """
    radius = 0.85

    def shape(u: float, v: float) -> Color | None:
        """Return the color of one point of the ghost."""
        if mode in ("normal", "eyes"):
            for eye_x in (-0.32, 0.32):
                dx, dy = u - eye_x, v + 0.2
                if dx * dx + dy * dy <= 0.27 ** 2:
                    px, py = dx - 0.11 * look[0], dy - 0.11 * look[1]
                    return BLUE if px * px + py * py <= 0.13 ** 2 else WHITE
            if mode == "eyes":
                return None
        if v <= 0:
            inside = u * u + v * v <= radius ** 2
        else:
            feet = 0.75 + 0.12 * math.cos(u / radius * 3 * math.pi)
            inside = abs(u) <= radius and v <= feet
        if not inside:
            return None
        if mode in ("scared", "flash"):
            for eye_x in (-0.3, 0.3):
                dx, dy = u - eye_x, v + 0.2
                if dx * dx + dy * dy <= 0.1 ** 2:
                    return PELLET if mode == "scared" else (255, 0, 0)
            return BLUE if mode == "scared" else WHITE
        return color

    return shape


def pellet_shape(radius: float) -> Shape:
    """Shape of a round pellet of the given radius."""

    def shape(u: float, v: float) -> Color | None:
        """Return the color of one point of the pellet."""
        return PELLET if u * u + v * v <= radius ** 2 else None

    return shape


class SpriteFactory:
    """Creates and remembers the pictures of one size."""

    def __init__(self, renderer: Renderer, size: int) -> None:
        """Prepare the factory; nothing is drawn until it is asked for."""
        self.renderer = renderer
        self.size = size
        self._cache: dict[tuple[object, ...], Image] = {}

    def _get(self, key: tuple[object, ...], shape: Shape) -> Image:
        """Return a cached picture, drawing it the first time."""
        if key not in self._cache:
            self._cache[key] = paint(self.renderer, self.size, shape)
        return self._cache[key]

    def pacman(self, direction: Direction, mouth: int) -> Image:
        """Pac-Man looking to a direction; mouth is 0 (closed) to 2 (wide)."""
        key = ("pacman", direction, mouth)
        return self._get(key, pacman_shape(direction,
                                           MOUTH_HALF_ANGLES[mouth]))

    def ghost(self, name: str, mode: str, look: tuple[int, int]) -> Image:
        """A ghost in a given mode, with the eyes looking to look."""
        color = GHOST_COLORS.get(name, GHOST_COLORS["Blinky"])
        if mode in ("scared", "flash"):
            look = (0, 0)
            name = "scared"
        return self._get(("ghost", name, mode, look),
                         ghost_shape(color, mode, look))

    def pacgum(self) -> Image:
        """A small pellet."""
        return self._get(("pacgum",), pellet_shape(0.14))

    def super_pacgum(self) -> Image:
        """A big pellet."""
        return self._get(("super",), pellet_shape(0.42))
