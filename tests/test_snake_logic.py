import random

from workshop.games.snake import GameScreen, LEFT, RIGHT, UP, SnakeModel


def test_reverse_direction_is_ignored() -> None:
    model = SnakeModel(width=20, height=12, rng=random.Random(1))
    model.change_direction(LEFT)
    assert model.direction == RIGHT
    model.change_direction(UP)
    assert model.direction == UP


def test_food_eating_grows_and_scores() -> None:
    model = SnakeModel(width=20, height=12, rng=random.Random(2))
    hx, hy = model.head
    model.food = (hx + 1, hy)

    before_length = model.length
    result = model.tick()

    assert result.alive is True
    assert result.ate_food is True
    assert model.score == 1
    assert model.length == before_length + 1


def test_wall_collision_ends_game() -> None:
    model = SnakeModel(width=12, height=8, rng=random.Random(3))
    model.body = [(11, 4), (10, 4), (9, 4), (8, 4)]
    model.direction = RIGHT
    model.food = (0, 0)

    result = model.tick()

    assert result.alive is False
    assert result.collision == "wall"
    assert model.alive is False


def test_self_collision_ends_game() -> None:
    model = SnakeModel(width=12, height=8, rng=random.Random(4))
    model.body = [(4, 2), (4, 3), (3, 3), (3, 2), (2, 2)]
    model.direction = LEFT
    model.food = (0, 0)

    result = model.tick()

    assert result.alive is False
    assert result.collision == "self"
    assert model.alive is False


def test_food_never_spawns_on_snake() -> None:
    model = SnakeModel(width=8, height=6, rng=random.Random(5))

    for _ in range(25):
        model.food = model._spawn_food()
        assert model.food not in set(model.body)


def test_wrap_mode_moves_through_edges() -> None:
    model = SnakeModel(width=12, height=8, rng=random.Random(6), wrap_mode=True)
    model.body = [(11, 4), (10, 4), (9, 4), (8, 4)]
    model.direction = RIGHT
    model.food = (0, 4)

    result = model.tick()

    assert result.alive is True
    assert result.ate_food is True
    assert model.head == (0, 4)


def test_speed_increases_with_score() -> None:
    screen = GameScreen()
    screen._model = SnakeModel(width=20, height=12, rng=random.Random(7))

    base_speed = screen._current_speed_cps()
    screen._model.score = 10
    boosted_speed = screen._current_speed_cps()

    assert boosted_speed > base_speed
