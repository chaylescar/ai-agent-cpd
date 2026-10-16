from random import Random

from workshop.games.snake import (
    Difficulty,
    Direction,
    SnakeLogic,
    _difficulty_for_key,
    _speed_for_difficulty,
    spawn_food_position,
)


def test_reverse_direction_is_ignored() -> None:
    logic = SnakeLogic(20, 10, Random(0))
    logic.set_direction(Direction.LEFT)
    assert logic.direction is Direction.RIGHT
    logic.set_direction(Direction.UP)
    assert logic.direction is Direction.UP


def test_quick_second_turn_into_neck_is_ignored() -> None:
    logic = SnakeLogic(20, 10, Random(0))
    logic.set_direction(Direction.UP)
    logic.set_direction(Direction.LEFT)
    assert logic.direction is Direction.UP

    start_head = logic.snake[0]
    logic.step()

    assert logic.alive
    assert logic.snake[0] == (start_head[0], start_head[1] - 1)


def test_growth_and_score_after_eating() -> None:
    logic = SnakeLogic(20, 10, Random(0))
    head_x, head_y = logic.snake[0]
    logic.food = (head_x + 1, head_y)

    start_len = logic.length
    logic.step()

    assert logic.alive
    assert logic.score == 1
    assert logic.length == start_len + 1
    assert logic.food not in set(logic.snake)


def test_wall_collision_sets_game_over() -> None:
    logic = SnakeLogic(6, 6, Random(0))
    logic.snake = [(5, 3), (4, 3), (3, 3)]
    logic.direction = Direction.RIGHT

    logic.step()

    assert not logic.alive


def test_wrap_mode_moves_across_edges() -> None:
    logic = SnakeLogic(6, 6, Random(0), wrap_mode=True)
    logic.snake = [(5, 3), (4, 3), (3, 3)]
    logic.direction = Direction.RIGHT

    logic.step()

    assert logic.alive
    assert logic.snake[0] == (0, 3)


def test_self_collision_sets_game_over() -> None:
    logic = SnakeLogic(8, 8, Random(0))
    logic.snake = [(3, 3), (3, 4), (2, 4), (2, 3), (2, 2), (3, 2)]
    logic.direction = Direction.DOWN

    logic.step()

    assert not logic.alive


def test_food_spawn_avoids_snake_cells() -> None:
    snake = [(0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2)]
    food = spawn_food_position(3, 3, snake, Random(0))
    assert food == (1, 1)


def test_difficulty_key_mapping_and_speed_order() -> None:
    assert _difficulty_for_key("1") is Difficulty.EASY
    assert _difficulty_for_key("2") is Difficulty.NORMAL
    assert _difficulty_for_key("3") is Difficulty.HARD
    assert _difficulty_for_key("9") is None

    easy = _speed_for_difficulty(Difficulty.EASY)
    normal = _speed_for_difficulty(Difficulty.NORMAL)
    hard = _speed_for_difficulty(Difficulty.HARD)
    assert easy < normal < hard
