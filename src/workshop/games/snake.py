"""Snake game screen and testable game logic."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from random import Random

from workshop.game import GameScreen as BaseGameScreen

Point = tuple[int, int]


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def delta(self) -> Point:
        return self.value


class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


def spawn_food_position(width: int, height: int, snake: list[Point], rng: Random) -> Point | None:
    occupied = set(snake)
    empties = [(x, y) for y in range(height) for x in range(width) if (x, y) not in occupied]
    if not empties:
        return None
    return rng.choice(empties)


@dataclass
class SnakeLogic:
    width: int
    height: int
    rng: Random
    wrap_mode: bool = False

    def __post_init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        cx = self.width // 2
        cy = self.height // 2
        self.snake: list[Point] = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = Direction.RIGHT
        self.pending_growth = 0
        self.score = 0
        self.alive = True
        self.food = spawn_food_position(self.width, self.height, self.snake, self.rng)

    @property
    def length(self) -> int:
        return len(self.snake)

    def set_direction(self, new_direction: Direction) -> None:
        if not self.alive:
            return
        if _is_opposite(self.direction, new_direction):
            return
        # Reject a turn that would move the head directly into the neck.
        if len(self.snake) > 1:
            dx, dy = new_direction.delta
            hx, hy = self.snake[0]
            if (hx + dx, hy + dy) == self.snake[1]:
                return
        self.direction = new_direction

    def step(self) -> None:
        if not self.alive:
            return

        dx, dy = self.direction.delta
        hx, hy = self.snake[0]
        next_head = (hx + dx, hy + dy)

        if self.wrap_mode:
            next_head = (next_head[0] % self.width, next_head[1] % self.height)
        elif not (0 <= next_head[0] < self.width and 0 <= next_head[1] < self.height):
            self.alive = False
            return

        body_to_check = set(self.snake if self.pending_growth > 0 else self.snake[:-1])
        if next_head in body_to_check:
            self.alive = False
            return

        ate_food = next_head == self.food
        self.snake.insert(0, next_head)

        if ate_food:
            self.score += 1
            self.pending_growth += 1
            self.food = spawn_food_position(self.width, self.height, self.snake, self.rng)

        if self.pending_growth > 0:
            self.pending_growth -= 1
        else:
            self.snake.pop()


def _is_opposite(current: Direction, proposed: Direction) -> bool:
    cdx, cdy = current.delta
    pdx, pdy = proposed.delta
    return cdx == -pdx and cdy == -pdy


class GameScreen(BaseGameScreen):
    TITLE = "SNAKE"
    COLS = 64
    ROWS = 28
    TICK_HZ = 11

    SNAKE_STYLE = "bold #46ff7a"
    FOOD_STYLE = "bold #ff6b4a"
    BORDER_STYLE = "bold #38d96f"
    TEXT_STYLE = "#b8ffcc"

    def on_start(self) -> None:
        self._rng = Random()
        self._field_x = 1
        self._field_y = 2
        self._field_w = self.COLS - 2
        self._field_h = self.ROWS - 3
        self._difficulty = Difficulty.NORMAL
        self._paused = False
        self._step_progress = 0.0
        self._logic = SnakeLogic(self._field_w, self._field_h, self._rng, wrap_mode=False)
        self._paint()

    def on_tick(self) -> None:
        if not self._logic.alive or self._paused:
            self._paint()
            return

        self._step_progress += _speed_for_difficulty(self._difficulty) / self.TICK_HZ
        while self._step_progress >= 1.0 and self._logic.alive:
            self._logic.step()
            self._step_progress -= 1.0
        self._paint()

    def on_game_key(self, key: str) -> None:
        if key == "p":
            if self._logic.alive:
                self._paused = not self._paused
            self._paint()
            return

        if key == "m":
            self._logic.wrap_mode = not self._logic.wrap_mode
            self._paint()
            return

        difficulty = _difficulty_for_key(key)
        if difficulty is not None:
            self._difficulty = difficulty
            self._paint()
            return

        if key == "r" and not self._logic.alive:
            self._logic.reset()
            self._paused = False
            self._step_progress = 0.0
            self._paint()
            return

        direction = _direction_for_key(key)
        if direction is not None:
            self._logic.set_direction(direction)
            self._paint()

    def _paint(self) -> None:
        self.grid.fill_rect(0, 0, self.COLS, self.ROWS, " ", "#041508")
        self.grid.draw_border(style=self.BORDER_STYLE)

        wrap = "ON" if self._logic.wrap_mode else "OFF"
        paused = " PAUSED" if self._paused and self._logic.alive else ""
        status = (
            f" SCORE {self._logic.score:03d}   LENGTH {self._logic.length:03d}"
            f"   SPEED {self._difficulty.value.upper():<6}   WRAP {wrap}{paused} "
        )
        self.grid.blit_text(2, 1, status[: self.COLS - 4], self.TEXT_STYLE)

        if self._logic.food is not None:
            fx, fy = self._logic.food
            self.grid.set_cell(self._field_x + fx, self._field_y + fy, "█", self.FOOD_STYLE)

        for index, (sx, sy) in enumerate(self._logic.snake):
            style = "bold #9bff6a" if index == 0 else self.SNAKE_STYLE
            self.grid.set_cell(self._field_x + sx, self._field_y + sy, "█", style)

        if not self._logic.alive:
            msg = " GAME OVER  R restart  Q menu "
            x = max(1, (self.COLS - len(msg)) // 2)
            y = self._field_y + (self._field_h // 2)
            self.grid.blit_text(x, y, msg, "bold #ffd37a")
        else:
            hint = " P pause  M wrap  1 easy 2 normal 3 hard "
            self.grid.blit_text(2, self.ROWS - 1, hint[: self.COLS - 4], "#6ddf90")


def _direction_for_key(key: str) -> Direction | None:
    mapping = {
        "up": Direction.UP,
        "down": Direction.DOWN,
        "left": Direction.LEFT,
        "right": Direction.RIGHT,
        "w": Direction.UP,
        "s": Direction.DOWN,
        "a": Direction.LEFT,
        "d": Direction.RIGHT,
    }
    return mapping.get(key)


def _difficulty_for_key(key: str) -> Difficulty | None:
    mapping = {
        "1": Difficulty.EASY,
        "2": Difficulty.NORMAL,
        "3": Difficulty.HARD,
    }
    return mapping.get(key)


def _speed_for_difficulty(difficulty: Difficulty) -> float:
    speeds = {
        Difficulty.EASY: 7.0,
        Difficulty.NORMAL: 11.0,
        Difficulty.HARD: 15.0,
    }
    return speeds[difficulty]
