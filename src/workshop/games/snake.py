"""Snake game screen for the workshop arcade."""

from __future__ import annotations

from dataclasses import dataclass
import random

from workshop.game import GameScreen as BaseGameScreen

Vec = tuple[int, int]

UP: Vec = (0, -1)
DOWN: Vec = (0, 1)
LEFT: Vec = (-1, 0)
RIGHT: Vec = (1, 0)


@dataclass
class TickResult:
    alive: bool
    ate_food: bool
    collision: str | None = None


class SnakeModel:
    """Pure game-state model used by the Textual screen and unit tests."""

    def __init__(
        self,
        width: int,
        height: int,
        rng: random.Random | None = None,
        wrap_mode: bool = False,
    ) -> None:
        if width < 8 or height < 6:
            raise ValueError("snake playfield must be at least 8x6")
        self.width = width
        self.height = height
        self._rng = rng or random.Random()
        self.wrap_mode = wrap_mode
        self.body: list[Vec] = []
        self.direction: Vec = RIGHT
        self.food: Vec | None = None
        self.score = 0
        self.alive = True
        self.collision: str | None = None
        self.restart()

    @property
    def head(self) -> Vec:
        return self.body[0]

    @property
    def length(self) -> int:
        return len(self.body)

    def restart(self) -> None:
        cx = self.width // 2
        cy = self.height // 2
        self.body = [(cx, cy), (cx - 1, cy), (cx - 2, cy), (cx - 3, cy)]
        self.direction = RIGHT
        self.score = 0
        self.alive = True
        self.collision = None
        self.food = self._spawn_food()

    def change_direction(self, requested: Vec) -> None:
        if requested == (0, 0):
            return
        # Reject 180-degree turns to avoid self-hit in a single keypress.
        if requested == (-self.direction[0], -self.direction[1]):
            return
        self.direction = requested

    def tick(self) -> TickResult:
        if not self.alive:
            return TickResult(alive=False, ate_food=False, collision=self.collision)

        hx, hy = self.head
        dx, dy = self.direction
        next_head = (hx + dx, hy + dy)

        if self.wrap_mode:
            next_head = (next_head[0] % self.width, next_head[1] % self.height)
        elif not (0 <= next_head[0] < self.width and 0 <= next_head[1] < self.height):
            self.alive = False
            self.collision = "wall"
            return TickResult(alive=False, ate_food=False, collision=self.collision)

        ate_food = self.food is not None and next_head == self.food
        occupied = self.body if ate_food else self.body[:-1]
        if next_head in occupied:
            self.alive = False
            self.collision = "self"
            return TickResult(alive=False, ate_food=False, collision=self.collision)

        self.body.insert(0, next_head)
        if ate_food:
            self.score += 1
            self.food = self._spawn_food()
        else:
            self.body.pop()

        return TickResult(alive=True, ate_food=ate_food)

    def _spawn_food(self) -> Vec | None:
        occupied = set(self.body)
        empty_cells = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in occupied
        ]
        if not empty_cells:
            return None
        return self._rng.choice(empty_cells)

    def toggle_wrap_mode(self) -> None:
        self.wrap_mode = not self.wrap_mode


class GameScreen(BaseGameScreen):
    TITLE = "SNAKE"
    COLS = 64
    ROWS = 24
    TICK_HZ = 11
    CELL_W = 2
    BASE_SPEED_CPS = 6.0
    SPEED_GAIN_PER_POINT = 0.4
    MAX_SPEED_CPS = 14.0

    def on_start(self) -> None:
        # Draw area is x=1..COLS-2 and y=3..ROWS-2 inside border and status line.
        # Terminal cells are taller than they are wide, so each logical game cell
        # spans two columns to keep movement speed feeling similar on both axes.
        self._model = SnakeModel(
            width=(self.COLS - 2) // self.CELL_W,
            height=self.ROWS - 4,
        )
        self._paused = False
        self._distance_accumulator = 0.0
        self._draw_scene()

    def on_tick(self) -> None:
        if self._paused or not self._model.alive:
            self._draw_scene()
            return

        # Simulate fractional movement distance so speed can scale with score.
        self._distance_accumulator += self._current_speed_cps() / self.TICK_HZ
        while self._distance_accumulator >= 1.0 and self._model.alive:
            self._model.tick()
            self._distance_accumulator -= 1.0

        self._draw_scene()

    def on_game_key(self, key: str) -> None:
        lowered = key.lower()
        if lowered == "p" and self._model.alive:
            self._paused = not self._paused
            self._draw_scene()
            return

        if lowered == "m":
            self._model.toggle_wrap_mode()
            self._draw_scene()
            return

        if lowered == "r" and not self._model.alive:
            self._model.restart()
            self._paused = False
            self._distance_accumulator = 0.0
            self._draw_scene()
            return

        direction = {
            "up": UP,
            "w": UP,
            "down": DOWN,
            "s": DOWN,
            "left": LEFT,
            "a": LEFT,
            "right": RIGHT,
            "d": RIGHT,
        }.get(lowered)
        if direction is not None and self._model.alive:
            self._model.change_direction(direction)
            self._draw_scene()

    def _current_speed_cps(self) -> float:
        speed = self.BASE_SPEED_CPS + self.SPEED_GAIN_PER_POINT * self._model.score
        return min(speed, self.MAX_SPEED_CPS)

    def _draw_scene(self) -> None:
        self.grid.fill_rect(0, 0, self.COLS, self.ROWS, " ", "#06120b")
        self.grid.draw_border(style="bold #52d273")

        mode = "WRAP" if self._model.wrap_mode else "WALL"
        pause_state = "PAUSED" if self._paused and self._model.alive else "RUN"
        speed = self._current_speed_cps()
        status = (
            f" SCORE {self._model.score:03d}   LENGTH {self._model.length:02d}"
            f"   SPD {speed:>4.1f}   {mode}   {pause_state} "
        )
        self.grid.blit_text(2, 1, status[: self.COLS - 4], "bold #9af2ab")

        divider_y = 2
        for x in range(1, self.COLS - 1):
            self.grid.set_cell(x, divider_y, "─", "#2f8f53")

        self.grid.fill_rect(1, 3, self.COLS - 2, self.ROWS - 4, " ", "#0a180f")

        if self._model.food is not None:
            fx, fy = self._model.food
            sx = 1 + fx * self.CELL_W
            sy = fy + 3
            self.grid.blit_text(sx, sy, "▓▓", "bold #ffb347")

        for index, (sx, sy) in enumerate(self._model.body):
            style = "bold #66ff66" if index == 0 else "#38c560"
            screen_x = 1 + sx * self.CELL_W
            screen_y = sy + 3
            self.grid.blit_text(screen_x, screen_y, "██", style)

        if not self._model.alive:
            game_over = " GAME OVER "
            hint = " R restart   M wrap mode   Q back to menu "
            score_line = f" FINAL SCORE {self._model.score} "
            x_game_over = max(2, (self.COLS - len(game_over)) // 2)
            x_hint = max(2, (self.COLS - len(hint)) // 2)
            x_score = max(2, (self.COLS - len(score_line)) // 2)
            y_mid = self.ROWS // 2
            self.grid.blit_text(x_game_over, y_mid - 1, game_over, "bold black on #ff6666")
            self.grid.blit_text(x_score, y_mid, score_line, "bold #ffd7a8")
            self.grid.blit_text(x_hint, y_mid + 1, hint, "#ffd7a8")
        elif self._paused:
            paused = " PAUSED "
            hint = " P resume   M wrap mode   Q back to menu "
            x_paused = max(2, (self.COLS - len(paused)) // 2)
            x_hint = max(2, (self.COLS - len(hint)) // 2)
            y_mid = self.ROWS // 2
            self.grid.blit_text(x_paused, y_mid - 1, paused, "bold black on #ffe066")
            self.grid.blit_text(x_hint, y_mid, hint, "#ffe7a8")
