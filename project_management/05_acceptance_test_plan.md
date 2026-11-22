# Acceptance test plan

Automatic tests: `make test` (107 tests) and `make lint`.
Manual tests: fill the *Result* column after trying each feature in the
real game (OK / KO + comment) and the date.

## Manual checks

| # | Feature | How to test | Expected | Result |
|---|---------|-------------|----------|--------|
| 1 | Launch | `python3 pac-man.py config.json` | Main menu with top 5 scores |ok |
| 2 | Wrong usage | No argument, two arguments | Usage message, no traceback | ok|
| 3 | Missing / broken config | Unknown file; `{ "lives":` | Clear message, no traceback |ok |
| 4 | Faulty values | `"lives": "abc"`, `"seed": 0`, `"level": 5` | Warnings and defaults |ko |
| 5 | Comments in config | `#` and `//` lines | Ignored |ok |
| 6 | Movement | Arrows and WASD | Pac-Man moves, walls stop it |ok |
| 7 | Pacgums and score | Eat a pacgum | +10, HUD updated |ok |
| 8 | Super-pacgum | Eat one in a corner | Ghosts blue and edible, +50 | ok|
| 9 | Eat a ghost | While edible | +200, eyes go to the corner, return after 5 s |ok |
| 10 | Lose a life | Touch a normal ghost | -1 life, everyone back to start |ok |
| 11 | Game over | Lose all lives | Game Over screen, name entry |ok |
| 12 | Highscore | Type a name, ENTER | Saved; shown in menu; survives restart |ok |
| 13 | Name rules | Type symbols / more than 10 characters | Ignored / limited to 10 |ok |
| 14 | Level complete | Eat everything (or cheat 5) | Next level, score and lives kept |ok |
| 15 | Victory | Finish the 10 levels (cheat 5 ten times) | Victory screen, name entry |ok |
| 16 | Time limit | Wait 90 s | -1 life, clock restarts |ok |
| 17 | Pause | P / ESC | Game stops; Resume and Return to main menu work |ok |
| 18 | Cheat mode | C, then 1 to 6 | Each cheat works; shown in the bar |ok |
| 19 | Corrupted highscores | Write garbage in `highscores.json` | Game starts with an empty table |ok |
| 20 | Maze generator failure | (simulated in tests) | Message in the menu |ok |
| 21 | Packaged game | Run the build from itch.io | Same behavior; editable `config.json` |ok |

## Bugs found and fixed during development

| Bug | How it was found | Fix |
|-----|------------------|-----|
| flake8 W292 (no newline at end of file) | `make lint` | Newline added. |
| Minimum maze size was 10 but the "42" needs 14 columns | Reading the generator code and testing sizes | `MIN_SIZE = 14`. |
| The center of the maze can be a solid cell of the "42" | Testing even sizes | Player starts in the closest free cell. |
| A player stopped by a wall slid between two cells when drawn | Reasoning about the drawing and a test | Previous cell reset when the player stops. |
| The "get ready" box hid Pac-Man | Looking at screenshots of the screens | Box moved to the upper part of the maze. |
| Skipping a level with the cheat key could crash if the generator failed | A test of generator failure in the middle of a game | The error is caught and the game goes back to the menu. |
