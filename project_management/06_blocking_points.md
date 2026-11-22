# Blocking points and conflicts

| Point | Description | How it was solved |
|-------|-------------|-------------------|
| Graphics library | The subject asks for MLX "or similar"; pygame has many more functions. | pygame used only through `renderer.py` with MLX-like operations; no circles (sprites painted pixel by pixel). |
| Generator documentation | The package README suggested coordinates as (row, column), but they are (x, y). | Checked with a real maze; documented in the README. |
| The "42" in the center | The generator draws closed cells in the middle, where the player should start. | Start in the closest free cell; pellets never placed in solid cells. |
| Dead ends | The few dead ends left by the generator are next to the "42". | Accepted: ghosts can turn back in dead ends. |
| Global random state | The generator re-seeds Python's `random`. | The game uses its own `random.Random`. |
| No window in automatic tests | Graphics cannot be seen in a test. | Tests with a hidden window (`SDL_VIDEODRIVER=dummy`) and visual checks of screenshots. |
| Windows build | PyInstaller builds for the system it runs on. | Build with Windows Python. |

## Conflicts

> Write here any disagreement or conflict (with teammates, with the
> evaluation requirements...) and how it was resolved. If there were none,
> say so.
