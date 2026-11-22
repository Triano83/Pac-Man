PAC-MAN  -  how to play
=======================

Start the game by running Pacman (Pacman.exe on Windows).

CONTROLS
  Arrow keys or WASD ... move
  P or ESC ............. pause (resume, or return to the main menu)
  UP / DOWN + ENTER .... choose an option in the menus
  C .................... cheat mode (for reviewers), then:
      1 invincible   2 freeze ghosts   3 faster player
      4 extra life   5 skip level      6 make ghosts edible

RULES
  - Eat every pacgum to finish the level. There are at least 10 levels.
  - Super-pacgums (the big dots in the corners) make the ghosts edible.
  - A ghost that touches you takes one life. Running out of time also
    takes one life.
  - When the game ends you can type your name (up to 10 letters,
    numbers or spaces) to save your score in the top 10.

CONFIGURATION
  Open config.json (next to the game) with any text editor.
  Lines that start with # are comments. You can change the number of
  lives, the points, the time per level, the maze size of each level, the
  seed of the first level and the highscore file name. Wrong or missing
  values are replaced by safe defaults and a message is logged.
