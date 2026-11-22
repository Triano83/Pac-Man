# Risk analysis

Probability and impact: L = low, M = medium, H = high.

| Risk | P | I | Mitigation |
|------|---|---|------------|
| The maze package is replaced by another one during peer review | H | H | All its use is in `maze.py`; the adapter validates what it receives and never assumes more than the documented interface. |
| The generator fails or returns a bad maze | M | H | Errors become `MazeError`; random mazes are retried; the menu shows a message instead of crashing. |
| The configuration is changed during the defense | H | M | No hard-coded game values; every value is validated, clamped or defaulted. |
| A corrupted highscore file | M | M | Defensive loading (skips bad lines), atomic saving, save errors only show a message. |
| The graphics library is not accepted as "similar to MLX" | M | H | pygame is used only through a small wrapper that offers MLX-like operations; a test checks that nothing else imports pygame. |
| A crash during the evaluation | M | H | Exceptions handled at every boundary (files, generator, window); a last barrier prints one line; tests cover the error paths. |
| The game is too hard or too easy | M | L | Speeds and times are constants; cheat mode helps the reviewer. |
| Code that the author cannot explain in the defense | M | H | Code written step by step with explanations; revision questions after each step; recode exercises practiced. |
| The packaged game does not work on the reviewer's computer | M | H | Build on the target operating system, run it before publishing, include a `config.json` and a help file inside the package. |
| The Windows build cannot be made from WSL | H | M | Build with Windows Python (`python build.py`). |
| Lost work | L | H | Frequent commits to the Git repository. |
