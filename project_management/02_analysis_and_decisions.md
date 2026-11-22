# Analysis of the subject and decisions

## Requirements found in the subject

- Python 3.10+, flake8, mypy, type hints, docstrings, `Makefile` rules.
- One argument: a JSON file with comments; no traceback ever.
- Maze from an assigned external package, used as-is (`PERFECT = False`).
- Persistent top 10 (names up to 10 alphanumeric characters or spaces).
- At least 10 levels, time limit, pause, menus, cheat mode.
- Graphics with MLX or a library whose functions all have an MLX
  equivalent.
- Public (unlisted) build, README in English, project management folder.

## Decisions

| Topic | Decision | Reason |
|-------|----------|--------|
| Graphics library | pygame, but only through `renderer.py`, using window, images, pixels, text and key events | The subject allows "MLX or similar" if every function has an MLX equivalent. One wrapper makes the rule easy to check and the library easy to replace. |
| Shapes | Sprites painted pixel by pixel | MLX has no circle function. |
| Separation | `game.py` knows nothing about the screen | The rules can be tested without a window and the interface only reads the state. |
| Time | `update(dt)` with elapsed time, characters move cell by cell at fixed intervals | Same speed on any computer; deterministic tests. |
| Maze package | Isolated in `maze.py` (adapter) | The package is replaced during peer review; the loader must adapt to it, not the opposite. |
| Maze validation | Check size, values and connectivity | A bad maze must never crash the game or trap the player. |
| Player start | Free cell closest to the center | The "42" drawing of the generator may occupy the exact center. |
| Minimum maze size | 14 | The "42" drawing needs at least 14x10 cells. |
| Highscore format | JSON list, atomic save | Readable, no dependencies, safe against interruptions. |
| Names | ASCII letters, digits and spaces; invalid characters ignored | "Alphanumeric" is ambiguous; ASCII avoids font problems. |
| Level completion | Eat all pacgums and super-pacgums | The foreword calls super-pacgums *Power Pellets*, and it is the original rule. |
| Time out | Lose one life and restart the clock | The subject leaves the choice open; it avoids restarting the whole level. |
| Ghosts | Walking distance (BFS), no U-turns, one personality each | Follows the foreword (Blinky chases, Pinky ambushes, Inky unpredictable, Clyde weird). |
| Own random generator | `random.Random` per game | The maze package re-seeds the global `random` module. |
| Cheat mode | Toggle with C, keys 1 to 6 | Lets a reviewer test every feature in a few minutes. |
| Packaging | PyInstaller, one folder, zip | Standard tool for Python; a launcher uses the `config.json` next to the executable. |
| Tests | pytest, including a random-play invariant test | Not graded, but they find bugs early. |
