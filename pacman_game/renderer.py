"""The only module that talks to pygame: a very small drawing layer.

The rest of the game uses only what is offered here, and each operation
has an equivalent in the MLX library:

    Renderer(width, height, title)  ->  mlx_init + mlx_new_window
    Renderer.clear                  ->  mlx_clear_window
    Renderer.new_image              ->  mlx_new_image
    Image.set_pixel / fill_rect     ->  writing pixels in the image buffer
    Renderer.put_image              ->  mlx_put_image_to_window
    Renderer.draw_text              ->  mlx_string_put
    Renderer.poll_events            ->  mlx_key_hook / mlx_hook (close)
    Renderer.present                ->  the window refresh of mlx_loop
"""
import time
from dataclasses import dataclass

import pygame

Color = tuple[int, int, int]
RGBA = tuple[int, int, int, int]

KEY_NAMES: dict[int, str] = {
    pygame.K_UP: "up",
    pygame.K_DOWN: "down",
    pygame.K_LEFT: "left",
    pygame.K_RIGHT: "right",
    pygame.K_RETURN: "enter",
    pygame.K_KP_ENTER: "enter",
    pygame.K_SPACE: "space",
    pygame.K_ESCAPE: "escape",
    pygame.K_BACKSPACE: "backspace",
}


class RendererError(Exception):
    """Raised when the window cannot be opened."""


@dataclass(frozen=True)
class KeyEvent:
    """A key pressed by the user.

    name is "up", "down", "left", "right", "enter", "space", "escape",
    "backspace" or the lowercase character of the key. char is the text
    typed (empty if the key does not type anything).
    """

    name: str
    char: str = ""


@dataclass(frozen=True)
class QuitEvent:
    """The user asked to close the window."""


InputEvent = KeyEvent | QuitEvent


class Image:
    """A picture in memory that can be drawn on and put on the window."""

    def __init__(self, width: int, height: int) -> None:
        """Create a fully transparent image."""
        self.width = width
        self.height = height
        self._surface = pygame.Surface((width, height), pygame.SRCALPHA)

    def set_pixel(self, x: int, y: int, color: RGBA) -> None:
        """Set the color of one pixel."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self._surface.set_at((x, y), color)

    def fill_rect(self, x: int, y: int, width: int, height: int,
                  color: Color | RGBA) -> None:
        """Fill a rectangle with one color."""
        self._surface.fill(color, (x, y, width, height))


class Renderer:
    """The game window."""

    def __init__(self, width: int, height: int, title: str) -> None:
        """Open the window.

        Raises:
            RendererError: If the window cannot be opened.
        """
        self.width = width
        self.height = height
        self._fonts: dict[int, pygame.font.Font] = {}
        try:
            pygame.display.init()
            pygame.font.init()
            self._screen = pygame.display.set_mode((width, height))
        except pygame.error as error:
            raise RendererError(
                f"Cannot open the game window: {error}") from error
        pygame.display.set_caption(title)

    def new_image(self, width: int, height: int) -> Image:
        """Create a transparent image."""
        return Image(width, height)

    def clear(self, color: Color) -> None:
        """Paint the whole window with one color."""
        self._screen.fill(color)

    def fill_rect(self, x: int, y: int, width: int, height: int,
                  color: Color) -> None:
        """Fill a rectangle of the window."""
        self._screen.fill(color, (x, y, width, height))

    def put_image(self, image: Image, x: int, y: int) -> None:
        """Draw an image with its top-left corner at (x, y)."""
        self._screen.blit(image._surface, (x, y))

    def _font(self, size: int) -> pygame.font.Font:
        """Return the (cached) font of a given pixel size."""
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(None, size)
        return self._fonts[size]

    def text_width(self, text: str, size: int) -> int:
        """Return the width in pixels of a text."""
        return int(self._font(size).size(text)[0])

    def draw_text(self, text: str, x: int, y: int, size: int,
                  color: Color, center: bool = False) -> None:
        """Write a text; y is its top. If center, x is the middle."""
        if not text:
            return
        picture = self._font(size).render(text, True, color)
        left = x - picture.get_width() // 2 if center else x
        self._screen.blit(picture, (left, y))

    def present(self) -> None:
        """Show on screen everything drawn since the last call."""
        pygame.display.flip()

    def poll_events(self) -> list[InputEvent]:
        """Return the key presses and close requests since the last call."""
        events: list[InputEvent] = []
        for raw in pygame.event.get():
            if raw.type == pygame.QUIT:
                events.append(QuitEvent())
            elif raw.type == pygame.KEYDOWN:
                char = raw.unicode if raw.unicode.isprintable() else ""
                name = KEY_NAMES.get(raw.key, char.lower())
                events.append(KeyEvent(name, char))
        return events

    def sleep(self, seconds: float) -> None:
        """Wait (used to keep a steady frame rate)."""
        if seconds > 0:
            time.sleep(seconds)

    def close(self) -> None:
        """Close the window."""
        pygame.display.quit()
        pygame.font.quit()
