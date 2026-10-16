"""Pong game screen and testable game logic."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

from workshop.game import GameScreen as BaseGameScreen


@dataclass
class PongLogic:
    width: int
    height: int
    rng: Random
    target_score: int = 5
    paddle_size: int = 4
    serve_speed_x: float = 0.7
    max_deflect_y: float = 0.65

    def __post_init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        center = (self.height - self.paddle_size) // 2
        self.left_y = float(center)
        self.right_y = float(center)
        self.left_score = 0
        self.right_score = 0
        self.winner: str | None = None
        self._serve(to_right=self.rng.choice([True, False]))

    def move_left(self, delta: int) -> None:
        self.left_y = self._clamp_paddle(self.left_y + delta)

    def move_right(self, delta: int) -> None:
        self.right_y = self._clamp_paddle(self.right_y + delta)

    def step(self) -> None:
        if self.winner is not None:
            return

        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        if self.ball_y <= 0:
            self.ball_y = 0
            self.ball_vy = abs(self.ball_vy)
        elif self.ball_y >= self.height - 1:
            self.ball_y = self.height - 1
            self.ball_vy = -abs(self.ball_vy)

        left_x = 2
        right_x = self.width - 3

        if self.ball_vx < 0 and self.ball_x <= left_x + 1 and self._hits_paddle(self.left_y):
            self.ball_x = left_x + 1
            self.ball_vx = abs(self.ball_vx)
            self.ball_vy = self._deflect(self.left_y)

        if self.ball_vx > 0 and self.ball_x >= right_x - 1 and self._hits_paddle(self.right_y):
            self.ball_x = right_x - 1
            self.ball_vx = -abs(self.ball_vx)
            self.ball_vy = self._deflect(self.right_y)

        if self.ball_x < 0:
            self.right_score += 1
            self._check_winner()
            if self.winner is None:
                self._serve(to_right=False)
        elif self.ball_x > self.width - 1:
            self.left_score += 1
            self._check_winner()
            if self.winner is None:
                self._serve(to_right=True)

    def _serve(self, to_right: bool) -> None:
        self.ball_x = self.width / 2
        self.ball_y = self.height / 2
        self.ball_vx = self.serve_speed_x if to_right else -self.serve_speed_x
        self.ball_vy = self.rng.uniform(-0.22, 0.22)

    def _clamp_paddle(self, y: float) -> float:
        return max(0.0, min(y, float(self.height - self.paddle_size)))

    def _hits_paddle(self, paddle_top: float) -> bool:
        return paddle_top <= self.ball_y < paddle_top + self.paddle_size

    def _deflect(self, paddle_top: float) -> float:
        center = paddle_top + self.paddle_size / 2
        rel = (self.ball_y - center) / (self.paddle_size / 2)
        rel = max(-1.0, min(1.0, rel))
        return rel * self.max_deflect_y

    def _check_winner(self) -> None:
        if self.left_score >= self.target_score:
            self.winner = "LEFT"
        elif self.right_score >= self.target_score:
            self.winner = "RIGHT"


class GameScreen(BaseGameScreen):
    TITLE = "PONG"
    COLS = 64
    ROWS = 28
    TICK_HZ = 20
    PADDLE_STEP = 2

    def on_start(self) -> None:
        self._field_x = 1
        self._field_y = 2
        self._field_w = self.COLS - 2
        self._field_h = self.ROWS - 3
        self._court_h = self._field_h - 2
        self._logic = PongLogic(self._field_w, self._court_h, Random())
        self._paint()

    def on_tick(self) -> None:
        self._logic.step()
        self._paint()

    def on_game_key(self, key: str) -> None:
        if key == "r" and self._logic.winner is not None:
            self._logic.reset()
            self._paint()
            return

        if self._logic.winner is not None:
            return

        if key == "w":
            self._logic.move_left(-self.PADDLE_STEP)
        elif key == "s":
            self._logic.move_left(self.PADDLE_STEP)
        elif key == "up":
            self._logic.move_right(-self.PADDLE_STEP)
        elif key == "down":
            self._logic.move_right(self.PADDLE_STEP)
        self._paint()

    def _paint(self) -> None:
        self.grid.fill_rect(0, 0, self.COLS, self.ROWS, " ", "#110d08")
        self.grid.draw_border(style="bold #ffcf66")

        fx = self._field_x
        fy = self._field_y
        fw = self._field_w

        for x in range(fx, fx + fw):
            self.grid.set_cell(x, fy, "━", "bold #ffc85a")
            self.grid.set_cell(x, fy + self._field_h - 1, "━", "bold #ffc85a")

        center_x = fx + fw // 2
        for y in range(fy + 1, fy + self._field_h - 1, 2):
            self.grid.set_cell(center_x, y, "│", "#a17a34")

        left_x = fx + 2
        right_x = fx + fw - 3
        left_top = fy + 1 + int(self._logic.left_y)
        right_top = fy + 1 + int(self._logic.right_y)
        for i in range(self._logic.paddle_size):
            self.grid.set_cell(left_x, left_top + i, "█", "bold #5de2ff")
            self.grid.set_cell(right_x, right_top + i, "█", "bold #ff8f69")

        ball_x = fx + int(round(self._logic.ball_x))
        ball_y = fy + 1 + int(round(self._logic.ball_y))
        self.grid.set_cell(ball_x, ball_y, "█", "bold #fff3cf")

        score = f" LEFT {self._logic.left_score}   RIGHT {self._logic.right_score} "
        self.grid.blit_text(max(2, (self.COLS - len(score)) // 2), 1, score, "#ffe3ad")
        self.grid.blit_text(2, self.ROWS - 1, "W/S left paddle  Arrow keys right paddle", "#d7b172")

        if self._logic.winner is not None:
            msg = f" {self._logic.winner} PLAYER WINS  R restart "
            self.grid.blit_text(
                max(2, (self.COLS - len(msg)) // 2), fy + self._field_h // 2, msg, "bold #ffd58a"
            )
