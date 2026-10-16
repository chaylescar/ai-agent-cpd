"""Tetris game screen and testable game logic."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

from workshop.game import GameScreen as BaseGameScreen

Point = tuple[int, int]

WELL_WIDTH = 10
WELL_HEIGHT = 20

PIECE_COLORS = {
    "I": "#5cd6ff",
    "J": "#6a7dff",
    "L": "#ffb15a",
    "O": "#ffe066",
    "S": "#76e089",
    "T": "#cf7bff",
    "Z": "#ff7b7b",
}

PIECES: dict[str, tuple[tuple[Point, ...], ...]] = {
    "I": (
        ((0, 1), (1, 1), (2, 1), (3, 1)),
        ((2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 2), (1, 2), (2, 2), (3, 2)),
        ((1, 0), (1, 1), (1, 2), (1, 3)),
    ),
    "J": (
        ((0, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (1, 2)),
        ((0, 1), (1, 1), (2, 1), (2, 2)),
        ((1, 0), (1, 1), (0, 2), (1, 2)),
    ),
    "L": (
        ((2, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (1, 2), (2, 2)),
        ((0, 1), (1, 1), (2, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
    ),
    "O": (
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
    ),
    "S": (
        ((1, 0), (2, 0), (0, 1), (1, 1)),
        ((1, 0), (1, 1), (2, 1), (2, 2)),
        ((1, 1), (2, 1), (0, 2), (1, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    "T": (
        ((1, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (2, 1), (1, 2)),
        ((0, 1), (1, 1), (2, 1), (1, 2)),
        ((1, 0), (0, 1), (1, 1), (1, 2)),
    ),
    "Z": (
        ((0, 0), (1, 0), (1, 1), (2, 1)),
        ((2, 0), (1, 1), (2, 1), (1, 2)),
        ((0, 1), (1, 1), (1, 2), (2, 2)),
        ((1, 0), (0, 1), (1, 1), (0, 2)),
    ),
}


@dataclass
class Piece:
    kind: str
    rotation: int
    x: int
    y: int


class TetrisLogic:
    def __init__(self, rng: Random, width: int = WELL_WIDTH, height: int = WELL_HEIGHT) -> None:
        self.rng = rng
        self.width = width
        self.height = height
        self.reset()

    def reset(self) -> None:
        self.board: list[list[str | None]] = [
            [None for _ in range(self.width)] for _ in range(self.height)
        ]
        self.score = 0
        self.lines = 0
        self.game_over = False
        self.current = self._spawn_piece()

    def tick(self) -> None:
        if self.game_over:
            return
        self.soft_drop()

    def move(self, dx: int) -> bool:
        if self.game_over:
            return False
        trial = Piece(self.current.kind, self.current.rotation, self.current.x + dx, self.current.y)
        if self._is_valid(trial):
            self.current = trial
            return True
        return False

    def rotate(self) -> bool:
        if self.game_over:
            return False
        trial = Piece(
            self.current.kind, (self.current.rotation + 1) % 4, self.current.x, self.current.y
        )
        if self._is_valid(trial):
            self.current = trial
            return True
        return False

    def soft_drop(self) -> bool:
        if self.game_over:
            return False
        trial = Piece(self.current.kind, self.current.rotation, self.current.x, self.current.y + 1)
        if self._is_valid(trial):
            self.current = trial
            return True
        self._lock_piece()
        return False

    def hard_drop(self) -> None:
        if self.game_over:
            return
        while self.soft_drop():
            pass

    def current_cells(self) -> list[Point]:
        return self._cells_for(self.current)

    def _spawn_piece(self) -> Piece:
        kind = self.rng.choice(tuple(PIECES.keys()))
        piece = Piece(kind=kind, rotation=0, x=3, y=0)
        if not self._is_valid(piece):
            self.game_over = True
        return piece

    def _lock_piece(self) -> None:
        for x, y in self.current_cells():
            if 0 <= y < self.height:
                self.board[y][x] = self.current.kind
        cleared = self.clear_full_rows()
        self.lines += cleared
        self.score += [0, 100, 300, 500, 800][cleared]
        self.current = self._spawn_piece()

    def clear_full_rows(self) -> int:
        keep_rows = [row for row in self.board if any(cell is None for cell in row)]
        cleared = self.height - len(keep_rows)
        if cleared <= 0:
            return 0
        new_rows = [[None for _ in range(self.width)] for _ in range(cleared)]
        self.board = new_rows + keep_rows
        return cleared

    def _cells_for(self, piece: Piece) -> list[Point]:
        shape = PIECES[piece.kind][piece.rotation]
        return [(piece.x + dx, piece.y + dy) for dx, dy in shape]

    def _is_valid(self, piece: Piece) -> bool:
        for x, y in self._cells_for(piece):
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                return False
            if self.board[y][x] is not None:
                return False
        return True


class GameScreen(BaseGameScreen):
    TITLE = "TETRIS"
    COLS = 64
    ROWS = 28
    TICK_HZ = 9

    def on_start(self) -> None:
        self._logic = TetrisLogic(Random())
        self._well_x = 8
        self._well_y = 3
        self._paint()

    def on_tick(self) -> None:
        self._logic.tick()
        self._paint()

    def on_game_key(self, key: str) -> None:
        if key == "r":
            self._logic.reset()
            self._paint()
            return
        if self._logic.game_over:
            return

        if key == "left":
            self._logic.move(-1)
        elif key == "right":
            self._logic.move(1)
        elif key in {"up", "x"}:
            self._logic.rotate()
        elif key == "down":
            self._logic.soft_drop()
        elif key == "space":
            self._logic.hard_drop()
        self._paint()

    def _paint(self) -> None:
        self.grid.fill_rect(0, 0, self.COLS, self.ROWS, " ", "#0d1016")
        self.grid.draw_border(style="bold #5e7cff")

        wx, wy = self._well_x, self._well_y
        self._draw_box(wx, wy, WELL_WIDTH + 2, WELL_HEIGHT + 2, "bold #6f88ff")
        self.grid.fill_rect(wx + 1, wy + 1, WELL_WIDTH, WELL_HEIGHT, " ", "#0a1320")

        for y, row in enumerate(self._logic.board):
            for x, cell in enumerate(row):
                if cell is not None:
                    self.grid.set_cell(wx + 1 + x, wy + 1 + y, "█", f"bold {PIECE_COLORS[cell]}")

        if not self._logic.game_over:
            for x, y in self._logic.current_cells():
                if 0 <= y < WELL_HEIGHT:
                    kind = self._logic.current.kind
                    self.grid.set_cell(wx + 1 + x, wy + 1 + y, "█", f"bold {PIECE_COLORS[kind]}")

        sx = wx + WELL_WIDTH + 5
        self.grid.blit_text(sx, wy + 1, f"SCORE {self._logic.score:05d}", "#d7e2ff")
        self.grid.blit_text(sx, wy + 3, f"LINES {self._logic.lines:05d}", "#d7e2ff")
        self.grid.blit_text(sx, wy + 6, "LEFT/RIGHT move", "#8da3ff")
        self.grid.blit_text(sx, wy + 7, "UP or X rotate", "#8da3ff")
        self.grid.blit_text(sx, wy + 8, "DOWN soft drop", "#8da3ff")
        self.grid.blit_text(sx, wy + 9, "SPACE hard drop", "#8da3ff")
        self.grid.blit_text(sx, wy + 10, "R restart", "#8da3ff")

        if self._logic.game_over:
            msg = " GAME OVER  R restart "
            self.grid.blit_text(wx - 1, wy + WELL_HEIGHT // 2, msg, "bold #ffd27f")

    def _draw_box(self, x: int, y: int, width: int, height: int, style: str) -> None:
        x2 = x + width - 1
        y2 = y + height - 1
        self.grid.set_cell(x, y, "┏", style)
        self.grid.set_cell(x2, y, "┓", style)
        self.grid.set_cell(x, y2, "┗", style)
        self.grid.set_cell(x2, y2, "┛", style)
        for px in range(x + 1, x2):
            self.grid.set_cell(px, y, "━", style)
            self.grid.set_cell(px, y2, "━", style)
        for py in range(y + 1, y2):
            self.grid.set_cell(x, py, "┃", style)
            self.grid.set_cell(x2, py, "┃", style)
