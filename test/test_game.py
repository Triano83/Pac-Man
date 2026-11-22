"""Tests for the game rules."""
import random

from pacman_game.config import GameConfig
from pacman_game.entities import Direction, GhostState
from pacman_game.game import (FRIGHTENED_TIME, PLAYER_INTERVAL, READY_TIME,
                              RESPAWN_TIME, Game, GameEvent, GameState)

DIRECTIONS = (Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT)


def make_game(**changes: int) -> Game:
    """Return a game ready to play (the 'ready' pause already finished)."""
    config = GameConfig(**changes)  # type: ignore[arg-type]
    game = Game(config, random.Random(1))
    game.ready_timer = 0.0
    return game


def advance(game: Game, seconds: float) -> list[GameEvent]:
    """Run the game for some seconds, in small steps; return the events."""
    events: list[GameEvent] = []
    for _ in range(round(seconds / 0.05)):
        events.extend(game.update(0.05))
    return events


def open_direction(game: Game) -> Direction:
    """Return a direction in which the player can move."""
    for direction in DIRECTIONS:
        if game.maze.can_move(game.player.x, game.player.y,
                              direction.wall_bit):
            return direction
    raise AssertionError("the player is enclosed")


def closed_direction(game: Game) -> Direction:
    """Return a direction blocked by a wall."""
    for direction in DIRECTIONS:
        if not game.maze.can_move(game.player.x, game.player.y,
                                  direction.wall_bit):
            return direction
    raise AssertionError("the player has no wall around")


def test_initial_state() -> None:
    """A new game follows the rules of the level structure."""
    game = Game(GameConfig(), random.Random(1))
    corners = game.maze.corners()
    assert game.lives == 3 and game.score == 0 and game.level_number == 1
    assert game.player.cell == game.maze.center_cell()
    assert [ghost.cell for ghost in game.ghosts] == corners
    assert game.super_pacgums == set(corners)
    assert game.player.cell not in corners
    assert len(game.pacgums) == len(game.maze.free_cells()) - 5
    assert game.ready_timer == READY_TIME


def test_first_level_is_always_the_same() -> None:
    """The first level uses the fixed seed of the configuration."""
    first = Game(GameConfig(), random.Random(1))
    second = Game(GameConfig(), random.Random(2))
    assert first.maze.cells == second.maze.cells


def test_ready_pause_blocks_movement() -> None:
    """Nobody moves during the 'ready' countdown."""
    game = Game(GameConfig(), random.Random(1))
    start = game.player.cell
    game.set_direction(open_direction(game))
    game.update(0.1)
    assert game.player.cell == start
    assert game.ready_timer < READY_TIME


def test_player_moves_and_eats() -> None:
    """Walking over a pacgum gives points and removes it."""
    game = make_game()
    before = len(game.pacgums)
    start = game.player.cell
    game.set_direction(open_direction(game))
    events = advance(game, PLAYER_INTERVAL + 0.05)
    assert game.player.cell != start
    assert GameEvent.PACGUM_EATEN in events
    assert game.score == game.config.points_per_pacgum
    assert len(game.pacgums) == before - 1


def test_player_cannot_cross_walls() -> None:
    """A wall stops the player."""
    game = make_game()
    start = game.player.cell
    game.set_direction(closed_direction(game))
    advance(game, 2.0)
    assert game.player.cell == start


def test_ghost_collision_costs_a_life() -> None:
    """After a hit everybody goes back to the start."""
    game = make_game()
    game.ghosts[2].place(*game.player.cell)
    events: list[GameEvent] = []
    game._check_collisions(events)
    assert GameEvent.LIFE_LOST in events
    assert game.lives == 2
    assert game.player.cell == game.player_start
    assert [g.cell for g in game.ghosts] == game.maze.corners()
    assert game.ready_timer == READY_TIME


def test_invincibility_cheat() -> None:
    """With invincibility a ghost does not take lives."""
    game = make_game()
    game.toggle_cheat_mode()
    game.cheat_toggle_invincible()
    game.ghosts[0].place(*game.player.cell)
    game._check_collisions([])
    assert game.lives == 3


def test_game_over() -> None:
    """Losing the last life ends the game for good."""
    game = make_game(lives=1)
    game.ghosts[0].place(*game.player.cell)
    events: list[GameEvent] = []
    game._check_collisions(events)
    assert game.state == GameState.GAME_OVER and game.lives == 0
    assert GameEvent.GAME_OVER in events
    assert game.update(1.0) == []


def test_super_pacgum_and_edible_ghosts() -> None:
    """A super-pacgum makes ghosts edible and eating one gives points."""
    game = make_game()
    corner = game.maze.corners()[0]
    game.player.place(*corner)
    events: list[GameEvent] = []
    game._eat_pellets(events)
    assert GameEvent.SUPER_PACGUM_EATEN in events
    assert game.score == game.config.points_per_super_pacgum
    assert all(g.state == GhostState.FRIGHTENED for g in game.ghosts)
    game._check_collisions(events)
    assert GameEvent.GHOST_EATEN in events
    assert game.score == (game.config.points_per_super_pacgum
                          + game.config.points_per_ghost)
    assert game.ghosts[0].state == GhostState.RESPAWNING
    assert game.ghosts[0].cell == game.ghosts[0].home
    assert game.lives == 3


def test_eaten_ghost_respawns() -> None:
    """An eaten ghost comes back after RESPAWN_TIME seconds."""
    game = make_game()
    game.toggle_cheat_mode()
    game.cheat_toggle_invincible()
    ghost = game.ghosts[1]
    ghost.state = GhostState.RESPAWNING
    ghost.respawn_timer = RESPAWN_TIME
    for _ in range(int(RESPAWN_TIME / 0.1) + 2):
        game.update(0.1)
    assert ghost.state == GhostState.CHASING


def test_frightened_time_ends() -> None:
    """Ghosts stop being edible when the time is over."""
    game = make_game()
    game.toggle_cheat_mode()
    game.cheat_frighten_ghosts()
    assert game.frightened_timer == FRIGHTENED_TIME
    game.frightened_timer = 0.05
    game.update(0.1)
    assert all(g.state == GhostState.CHASING for g in game.ghosts)


def test_time_up_costs_a_life() -> None:
    """When the clock reaches zero a life is lost and the clock restarts."""
    game = make_game()
    game.time_left = 0.05
    events = game.update(0.1)
    assert GameEvent.TIME_UP in events
    assert game.lives == 2
    assert game.time_left == game.config.level_max_time


def test_completing_a_level() -> None:
    """Eating the last pellet moves to the next level, keeping the score."""
    game = make_game()
    target = game.maze.neighbors(*game.player.cell)[0]
    direction = next(d for d in DIRECTIONS
                     if (game.player.x + d.dx,
                         game.player.y + d.dy) == target)
    game.pacgums = {target}
    game.super_pacgums = set()
    game.set_direction(direction)
    events = advance(game, PLAYER_INTERVAL + 0.05)
    assert GameEvent.LEVEL_COMPLETE in events
    assert game.level_number == 2
    assert game.score == game.config.points_per_pacgum
    assert game.lives == 3
    assert 0 < game.ready_timer <= READY_TIME
    assert game.state == GameState.PLAYING


def test_victory_after_the_last_level() -> None:
    """Completing every level wins the game."""
    game = make_game()
    game.toggle_cheat_mode()
    events: list[GameEvent] = []
    for _ in range(game.total_levels):
        events = game.cheat_skip_level()
    assert GameEvent.VICTORY in events
    assert game.state == GameState.VICTORY
    assert game.cheat_skip_level() == []


def test_at_least_ten_levels() -> None:
    """The default configuration has the 10 levels the subject asks."""
    assert Game(GameConfig(), random.Random(1)).total_levels >= 10


def test_pause() -> None:
    """Nothing changes while the game is paused."""
    game = make_game()
    start = game.player.cell
    game.set_direction(open_direction(game))
    game.toggle_pause()
    assert game.paused
    time_before = game.time_left
    game.update(1.0)
    assert game.player.cell == start and game.time_left == time_before
    game.toggle_pause()
    assert not game.paused


def test_cheats_need_cheat_mode() -> None:
    """Cheats do nothing while the cheat mode is off."""
    game = make_game()
    game.cheat_extra_life()
    game.cheat_toggle_invincible()
    game.cheat_toggle_freeze()
    game.cheat_toggle_speed()
    assert game.lives == 3
    assert not (game.invincible or game.ghosts_frozen or game.fast_player)
    assert game.cheat_skip_level() == []
    assert game.level_number == 1


def test_cheats_work_and_reset() -> None:
    """Cheats work in cheat mode and switch off with it."""
    game = make_game()
    game.toggle_cheat_mode()
    game.cheat_extra_life()
    game.cheat_toggle_invincible()
    game.cheat_toggle_freeze()
    game.cheat_toggle_speed()
    assert game.lives == 4
    assert game.invincible and game.ghosts_frozen and game.fast_player
    game.toggle_cheat_mode()
    assert not (game.invincible or game.ghosts_frozen or game.fast_player)


def test_frozen_ghosts_do_not_move() -> None:
    """Frozen ghosts stay in their corners."""
    game = make_game()
    game.toggle_cheat_mode()
    game.cheat_toggle_freeze()
    for _ in range(30):
        game.update(0.1)
    assert [g.cell for g in game.ghosts] == game.maze.corners()


def test_ghosts_leave_their_corners() -> None:
    """Without cheats the ghosts move around."""
    game = make_game()
    game.toggle_cheat_mode()
    game.cheat_toggle_invincible()
    for _ in range(20):
        game.update(0.1)
    assert any(g.cell != g.home for g in game.ghosts)


def test_random_play_keeps_the_rules() -> None:
    """Thousands of random steps never break the basic invariants."""
    game = make_game(level_max_time=3600)
    game.toggle_cheat_mode()
    game.cheat_toggle_invincible()
    rng = random.Random(7)
    last_score = 0
    for step in range(6000):
        if step % 8 == 0:
            game.set_direction(rng.choice(DIRECTIONS))
        if step % 500 == 0:
            game.cheat_frighten_ghosts()
        game.update(0.05)
        maze = game.maze
        actors = [game.player, *game.ghosts]
        for actor in actors:
            assert maze.in_bounds(actor.x, actor.y)
            assert not maze.is_solid(actor.x, actor.y)
            previous = (actor.prev_x, actor.prev_y)
            if previous != actor.cell:
                assert previous in maze.neighbors(*actor.cell)
        assert game.score >= last_score
        assert game.lives >= 0
        last_score = game.score


def test_blinky_catches_a_standing_player() -> None:
    """The chasing ghosts really come for the player."""
    game = make_game()
    game.toggle_cheat_mode()
    game.cheat_toggle_invincible()
    caught = False
    for _ in range(600):
        game.update(0.05)
        if game.ghosts[0].cell == game.player.cell:
            caught = True
            break
    assert caught


def test_stopped_player_does_not_slide() -> None:
    """A player stopped by a wall is drawn in its cell, not between two."""
    game = make_game()
    game.set_direction(closed_direction(game))
    advance(game, 1.0)
    assert (game.player.prev_x, game.player.prev_y) == game.player.cell
    assert 0.0 <= game.player_progress() <= 1.0
    assert 0.0 <= game.ghost_progress(game.ghosts[0]) <= 1.0
