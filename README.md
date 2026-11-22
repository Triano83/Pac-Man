*This project has been created as part of the 42 curriculum by Jotriano and sllabres.*

# Pac-Man

## Description

A complete and playable **Pac-Man** written in Python 3.10+, with
object-oriented code, a very small graphics layer (pygame, restricted to
functions that have an MLX equivalent) and a modular architecture.

Goal of the project: recreate the arcade classic with a clean project
structure, automatic checks (flake8, mypy, pytest), a configuration file,
a persistent highscore table, mazes produced by an external generator
(the assigned *A-Maze-ing* package, used as-is) and a standalone build
that can be published on itch.io.

Overview of the game:

- A maze with walls and corridors, a pacgum in almost every corridor cell
  and a super-pacgum in each of the four corners.
- Four ghosts, one per corner, each with its own behavior (Blinky chases,
  Pinky ambushes, Inky is unpredictable, Clyde is "weird").
- The player starts in the middle of the maze with 3 lives.
- At least 10 levels with a time limit; lives and score are kept between
  levels.
- Main menu, in-game HUD, pause menu, game over and victory screens,
  top 10 highscores and a cheat mode for reviewers.

## Instructions

### Requirements

- Python 3.10 or later and `make`.
- A graphical environment (on Windows with WSL you need WSLg).

### Installation and execution

```bash
python3 -m venv .venv
source .venv/bin/activate
make install        # pygame, flake8, mypy, pytest and the maze generator
make run            # same as: python3 pac-man.py config.json
```

The program takes **exactly one argument**: a JSON configuration file.
Every error (missing file, invalid JSON...) is reported with a clear
message and never with a Python traceback. Set `PACMAN_DEBUG=1` to see
the full error while developing.

### Makefile rules

| Rule | What it does |
|------|--------------|
| `make install` | Installs the dependencies (including the maze generator wheel). |
| `make run` | Runs the game with `config.json`. |
| `make debug` | Runs the game under `pdb`. |
| `make clean` | Removes `__pycache__`, `.mypy_cache`, `.pytest_cache`, `build`, `dist`. |
| `make lint` | `flake8 .` and `mypy .` with the flags required by the subject. |
| `make lint-strict` | `flake8 .` and `mypy . --strict` (optional, see *Known limitations*). |
| `make test` | Runs the automatic tests (`pytest`). |
| `make package` | Builds the standalone game with PyInstaller (see *Packaging*). |

### Controls

| Key | Action |
|-----|--------|
| Arrow keys or WASD | Move (ZQSD also works on AZERTY keyboards) |
| P or ESC | Pause / resume |
| UP / DOWN + ENTER or SPACE | Choose an option in the menus |
| C | Turn the cheat mode on / off |

### Cheat mode

Press **C** during a game. The bottom bar lists the cheats and shows the
active ones in green:

| Key | Cheat |
|-----|-------|
| 1 | Invincibility (ghosts cannot take lives) |
| 2 | Freeze the ghosts |
| 3 | Faster player |
| 4 | One extra life |
| 5 | Skip (win) the current level |
| 6 | Make the ghosts edible |

Turning the cheat mode off also switches off the toggled cheats.

### Packaging

The standalone game is built with [PyInstaller](https://pyinstaller.org/).
It must be built on the operating system it is meant for (a Windows build
must be made on Windows):

```bash
pip install pyinstaller
python build.py          # or: make package
```

This creates `dist/Pacman/` (the game folder) and `dist/Pacman.zip` (ready
to upload). The recipe is `pacman.spec`, `launcher.py` starts the packaged
game using the `config.json` placed next to the executable, and
`PLAYER_README.txt` is the in-package help (controls, options and
configuration).

Public build: **TODO: add the link of the unlisted itch.io page here.**

## Configuration

The configuration file is JSON with comments: lines starting with `#` or
`//` are ignored. A complete example is `config.json`.

| Key | Default | Valid values | Meaning |
|-----|---------|--------------|---------|
| `highscore_filename` | `"highscores.json"` | non-empty string | File where the top 10 is stored. |
| `level` | 10 levels of 20x20 | list of `{"width", "height"}` | One entry per level. Each size must be between 14 and 50. If fewer than 10 levels are given, default levels are added. |
| `lives` | 3 | 1 - 99 | Lives at the start. |
| `points_per_pacgum` | 10 | 0 - 10000 | Points for a pacgum. |
| `points_per_super_pacgum` | 50 | 0 - 10000 | Points for a super-pacgum. |
| `points_per_ghost` | 200 | 0 - 10000 | Points for an edible ghost. |
| `seed` | 42 | 1 - 2147483647 | Seed of the maze of level 1 (the other levels are random). |
| `level_max_time` | 90 | 10 - 3600 | Seconds available in each level. |

Faulty configurations:

- A **missing or invalid value** (wrong type) is replaced by its default
  and a warning is logged.
- A number **out of range** is clamped to the nearest valid value and a
  warning is logged.
- **Unknown keys are ignored.**
- A file that cannot be used at all (missing, not `.json`, not valid
  UTF-8, broken JSON, not an object) stops the program with a clear
  message.

Notes: the subject suggests a `pacgum` key, which is not used because the
pellets fill every free corridor cell. The minimum maze size is 14 because
the generator needs at least 14x10 cells to draw its "42" pattern.

## Highscore

The top 10 is stored in a **JSON file** (a list of `{"name", "score"}`
objects) whose name comes from the configuration.

- It is loaded when the program starts and saved when a game ends (win or
  lose), after the player types a name. It is also shown in the main menu
  (top 5) and in the *View Highscores* screen (top 10).
- Names: at most 10 characters, only ASCII letters, digits and spaces.
  Invalid characters typed by the player are ignored; an empty name
  becomes `Player`. Scores are non-negative integers.
- Ties: the older score stays above the newer one.
- **Robustness:** a missing file, an unreadable file, invalid JSON or a
  wrong structure give an empty table; invalid lines are skipped and
  logged. Saving writes a temporary file and then renames it
  (`os.replace`), so an interruption cannot leave a half-written file, and
  a failure to save only shows a message.

*Why JSON?* It is human readable, needs no extra dependency, is easy to
validate line by line and matches what the subject suggests.

## Maze Generation

Mazes are produced by the assigned **A-Maze-ing** package
(`mazegenerator` 2.1.0, wheel in the root of the repository), used
**as-is**, without modifying it. Only `pacman_game/maze.py` knows about it
(an adapter), so another package could be plugged in by changing that
file alone.

- `generate_maze(width, height, seed)` calls
  `MazeGenerator(size=(width, height), perfect=False, seed=seed)`.
  `perfect=False` removes dead ends and creates loops, which Pac-Man
  needs.
- Level 1 uses the `seed` of the configuration; the following levels use
  seed 0, which means a random maze. If a random maze fails, up to 3
  attempts are made.
- The adapter validates what it receives (size, cell values 0-15) and
  checks that every free cell is reachable (breadth-first search). Any
  problem, or any exception of the package, becomes a `MazeError`: when it
  happens the menu shows a message or the game goes back to the menu; the
  program never crashes.
- Facts learnt about the package: cells are bitmasks (north = 1,
  east = 2, south = 4, west = 8, a bit set means *wall*); coordinates are
  `(x, y)` and the maze is indexed `maze[y][x]`; the "42" drawing is made
  of closed cells (value 15), placed in the center of the maze and only if
  the maze is at least 14x10; it re-seeds Python's global `random`
  module, so the game uses its own `random.Random` instance; the few dead
  ends left are the ones next to the "42".
- Because the center of the maze can be part of the "42", the player
  starts in the free cell closest to the center. Pacgums are placed in
  every free cell except the player's start and the four corners, where
  the super-pacgums are.

## Implementation

- **Time:** the game is updated with `update(dt)`, where `dt` is the time
  elapsed since the last frame (capped at 0.1 s). Every character crosses
  one cell every fixed time (player 0.15 s; ghosts slower, a bit faster
  every level but never as fast as the player). The result is the same on
  a fast or slow computer, and the logic can be tested without a window.
- **Movement:** by cells. The key pressed is remembered as the *wanted*
  direction, so turns made before a crossing are applied as soon as there
  is no wall. For drawing, every character keeps its previous cell and the
  fraction of the way done, so the screen shows a smooth slide.
- **Ghosts** (`ghost_ai.py`): they use the real walking distance (breadth
  first search), never turn back unless in a dead end, and break ties at
  random. Blinky goes to the player; Pinky to the cell up to 4 steps
  ahead of the player; Inky chases half of the time and wanders the rest;
  Clyde chases from far away but goes back to his corner when closer than
  8 cells. Edible ghosts run away from the player.
- **Rules:** a super-pacgum makes ghosts edible for 8 s; an eaten ghost
  waits 5 s in its corner (shown as eyes) and comes back. A hit sends
  everyone back to their start with a 2 s "get ready" pause. A level is
  completed when all pacgums *and* super-pacgums are eaten. **When the
  time of a level ends, a life is lost** and the clock restarts (the
  subject lets us choose). The score never decreases.
- **Events:** `Game.update()` returns what happened (pacgum eaten, life
  lost, level complete...) so that the interface can show messages.
- **Drawing without circles:** MLX has no circle function, so Pac-Man,
  ghosts and pellets are painted pixel by pixel into images the first time
  they are needed (smoothing the edges by sampling) and then reused.
- **Errors:** user input and files are always validated; resources are
  handled with `with`; the entry point has a last barrier that prints one
  line instead of a traceback.

## General Software Architecture

```
pac-man.py ──► pacman_game/cli.py ──► config.py       (read + validate JSON)
 launcher.py ─┘        │           ├─► highscores.py  (top 10 file)
 (packaged game)       │           └─► app.py ───────► views.py ──► sprites.py
                       │                  │               │            │
                       │                  ▼               ▼            ▼
                       │               game.py        renderer.py (only pygame)
                       │                  │
                       │          ┌───────┴────────┐
                       │      ghost_ai.py      entities.py
                       │          └───────┬────────┘
                       └──────────────────► maze.py ──► mazegenerator (external)
```

| Module | Responsibility |
|--------|----------------|
| `config.py` | Reads the JSON with comments, validates every value, defaults. |
| `maze.py` | `Maze` data structure (walls, neighbors, distances) and the adapter to the external generator. |
| `entities.py` | `Direction`, `Actor`, `Player`, `Ghost`, `GhostState`. |
| `ghost_ai.py` | Decides the next cell of a ghost (one personality each). |
| `game.py` | All the rules: levels, pellets, score, lives, time, cheats. **It does not know the screen.** |
| `highscores.py` | Top 10: validation, sorting, persistence. |
| `renderer.py` | The only module that imports pygame: window, images, text, keys. |
| `sprites.py` | Pixel-by-pixel pictures (Pac-Man, ghosts, pellets), cached. |
| `views.py` | Draws the maze, the characters and the HUD from a `Game`. |
| `app.py` | Scenes (menu, instructions, highscores, game, pause, name entry) and the main loop. |
| `cli.py` | Arguments, error messages and start-up. |

The rules (`game.py`) and the screen (`app.py`, `views.py`) only talk
through a small interface: the screen sends keys and elapsed time, and
reads the state to draw it. That separation is what allows testing the
whole game without opening a window.

### Tests

`make test` runs 107 automatic tests (pytest, not part of the submission
rules): maze adapter, highscores (including corrupted files), game rules,
ghost behaviors, scenes and keys (with a hidden window), command line
errors, and a random-play test that checks that nobody crosses a wall.

## Known limitations

- `make lint` passes. `make lint-strict` (optional) reports a few
  messages: the maze package has no type information, and some strict
  checks give false positives.
- The game was developed on Windows with WSL. The packaging recipe was
  verified by building and running the game on Linux; the Windows build
  must be made, and checked, on Windows.
- The speeds and times that define the difficulty are constants at the top
  of `game.py` and can be tuned.

## Project Management

The planning and evidence documents are in
[`project_management/`](project_management/): timeline and progress,
analysis and decisions, risk analysis, team organization, acceptance test
plan and blocking points.

## Resources

References:

- [Python documentation](https://docs.python.org/3/): `dataclasses`, `enum`,
  `json`, `pathlib`, `typing`, `collections.deque`.
- [PEP 8](https://peps.python.org/pep-0008/),
  [PEP 257](https://peps.python.org/pep-0257/),
  [PEP 484](https://peps.python.org/pep-0484/).
- [flake8](https://flake8.pycqa.org/), [mypy](https://mypy.readthedocs.io/),
  [pytest](https://docs.pytest.org/).
- [pygame documentation](https://www.pygame.org/docs/).
- [PyInstaller manual](https://pyinstaller.org/en/stable/).
- [itch.io creator documentation](https://itch.io/docs/creators/).
- Jamey Pittman, *The Pac-Man Dossier* (behavior of the original ghosts).
- Breadth-first search (shortest paths in a grid).

### Use of AI

Claude (Anthropic) was used as a learning assistant, step by step:

- To translate and explain the subject, which is written in English.
- To propose the architecture and the order of the work.
- To write a first version of the code and of the tests of each module,
  which was then run, tested and explained before being kept.
- To explain errors and decisions (for example why ghosts use walking
  distances, or how the pixel sprites are built).
- To draft the documents of this repository (README and project
  management), which were then reviewed and completed by the author.

All AI-generated content was checked by running the linters and the tests
and by playing the game, and the author can explain every module.
