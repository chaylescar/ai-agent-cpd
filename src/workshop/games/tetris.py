"""Tetris game screen and pure logic helpers for workshop tests."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

from workshop.game import GameScreen as BaseGameScreen

WELL_WIDTH = 10
WELL_HEIGHT = 20

BLOCK_GLYPH = "██"
CELL_WIDTH = 2

LINE_SCORES = {
    0: 0,
    1: 100,
    2: 300,
    3: 500,
    4: 800,
}

PIECE_COLORS = {
    "I": "#44d9ff",
    "O": "#ffe066",
    "T": "#c792ea",
    "S": "#7bdc65",
    "Z": "#ff6b6b",
    "J": "#5c7cfa",
    "L": "#ffb347",
}

# Four precomputed orientations for each tetromino.
SHAPES: dict[str, tuple[tuple[tuple[int, int], ...], ...]] = {
    "I": (
        ((0, 1), (1, 1), (2, 1), (3, 1)),
        ((2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 2), (1, 2), (2, 2), (3, 2)),
        ((1, 0), (1, 1), (1, 2), (1, 3)),
    ),
    "O": (
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
    ),
    "T": (
        ((1, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (2, 1), (1, 2)),
        ((0, 1), (1, 1), (2, 1), (1, 2)),
        ((1, 0), (0, 1), (1, 1), (1, 2)),
    ),
    "S": (
        ((1, 0), (2, 0), (0, 1), (1, 1)),
        ((1, 0), (1, 1), (2, 1), (2, 2)),
        ((1, 1), (2, 1), (0, 2), (1, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    "Z": (
        ((0, 0), (1, 0), (1, 1), (2, 1)),
        ((2, 0), (1, 1), (2, 1), (1, 2)),
        ((0, 1), (1, 1), (1, 2), (2, 2)),
        ((1, 0), (0, 1), (1, 1), (0, 2)),
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
}


@dataclass
class Piece:
    kind: str
    x: int
    y: int
    rotation: int = 0


Board = list[list[str | None]]


def empty_board(width: int = WELL_WIDTH, height: int = WELL_HEIGHT) -> Board:
    return [[None for _ in range(width)] for _ in range(height)]


def piece_cells(piece: Piece) -> list[tuple[int, int]]:
    return [
        (piece.x + cx, piece.y + cy)
        for cx, cy in SHAPES[piece.kind][piece.rotation]
    ]


def can_place(board: Board, piece: Piece) -> bool:
    height = len(board)
    width = len(board[0]) if height else 0
    for x, y in piece_cells(piece):
        if x < 0 or x >= width or y < 0 or y >= height:
            return False
        if board[y][x] is not None:
            return False
    return True


def try_move(board: Board, piece: Piece, dx: int, dy: int) -> bool:
    moved = Piece(piece.kind, piece.x + dx, piece.y + dy, piece.rotation)
    if not can_place(board, moved):
        return False
    piece.x = moved.x
    piece.y = moved.y
    return True


def try_rotate(board: Board, piece: Piece) -> bool:
    rotated = Piece(piece.kind, piece.x, piece.y, (piece.rotation + 1) % 4)
    if not can_place(board, rotated):
        return False
    piece.rotation = rotated.rotation
    return True


def lock_piece(board: Board, piece: Piece) -> None:
    for x, y in piece_cells(piece):
        board[y][x] = piece.kind


def clear_full_rows(board: Board) -> int:
    width = len(board[0]) if board else 0
    kept = [row[:] for row in board if any(cell is None for cell in row)]
    cleared = len(board) - len(kept)
    new_rows = [[None for _ in range(width)] for _ in range(cleared)]
    board[:] = new_rows + kept
    return cleared


class TetrisLogic:
    """Pure game-state machine used by GameScreen and tests."""

    def __init__(self, rng: Random | None = None) -> None:
        self.rng = rng or Random()
        self.restart()

    def restart(self) -> None:
        self.board = empty_board()
        self.score = 0
        self.lines = 0
        self.game_over = False
        self.current = self._spawn_piece()
        if self.current is None:
            self.game_over = True

    def _spawn_piece(self) -> Piece | None:
        kind = self.rng.choice(tuple(SHAPES.keys()))
        piece = Piece(kind=kind, x=3, y=0, rotation=0)
        if not can_place(self.board, piece):
            return None
        return piece

    def move_left(self) -> bool:
        if self.game_over or self.current is None:
            return False
        return try_move(self.board, self.current, -1, 0)

    def move_right(self) -> bool:
        if self.game_over or self.current is None:
            return False
        return try_move(self.board, self.current, 1, 0)

    def rotate(self) -> bool:
        if self.game_over or self.current is None:
            return False
        return try_rotate(self.board, self.current)

    def soft_drop(self) -> bool:
        if self.game_over or self.current is None:
            return False
        if try_move(self.board, self.current, 0, 1):
            self.score += 1
            return True
        self._lock_and_continue()
        return False

    def hard_drop(self) -> int:
        if self.game_over or self.current is None:
            return 0
        steps = 0
        while try_move(self.board, self.current, 0, 1):
            steps += 1
        self.score += steps * 2
        self._lock_and_continue()
        return steps

    def tick(self) -> None:
        if self.game_over or self.current is None:
            return
        if not try_move(self.board, self.current, 0, 1):
            self._lock_and_continue()

    def _lock_and_continue(self) -> None:
        if self.current is None:
            return
        lock_piece(self.board, self.current)
        cleared = clear_full_rows(self.board)
        self.lines += cleared
        self.score += LINE_SCORES[cleared]
        self.current = self._spawn_piece()
        if self.current is None:
            self.game_over = True


class GameScreen(BaseGameScreen):
    TITLE = "TETRIS"
    COLS = 48
    ROWS = 24
    TICK_HZ = 5

    def on_start(self) -> None:
        self.logic = TetrisLogic()
        self._draw_game()

    def on_tick(self) -> None:
        self.logic.tick()
        self._draw_game()

    def on_game_key(self, key: str) -> None:
        if key == "r":
            self.logic.restart()
            self._draw_game()
            return
        if self.logic.game_over:
            self._draw_game()
            return

        if key == "left":
            self.logic.move_left()
        elif key == "right":
            self.logic.move_right()
        elif key in {"up", "x"}:
            self.logic.rotate()
        elif key == "down":
            self.logic.soft_drop()
        elif key == "space":
            self.logic.hard_drop()

        self._draw_game()

    def _draw_game(self) -> None:
        self.grid.clear(" ", "#031403")
        self.grid.draw_border(style="bold #33ff33")

        well_x = 3
        well_y = 2
        rendered_well_width = (WELL_WIDTH * CELL_WIDTH) + 2
        self._draw_box(well_x, well_y, rendered_well_width, WELL_HEIGHT + 2, "bold #33ff33")

        for y, row in enumerate(self.logic.board):
            for x, cell in enumerate(row):
                if cell is None:
                    continue
                self.grid.blit_text(
                    well_x + 1 + (x * CELL_WIDTH),
                    well_y + 1 + y,
                    BLOCK_GLYPH,
                    f"bold {PIECE_COLORS[cell]}",
                )

        if self.logic.current is not None:
            for x, y in piece_cells(self.logic.current):
                self.grid.blit_text(
                    well_x + 1 + (x * CELL_WIDTH),
                    well_y + 1 + y,
                    BLOCK_GLYPH,
                    f"bold {PIECE_COLORS[self.logic.current.kind]}",
                )

        status_x = well_x + rendered_well_width + 3
        self.grid.blit_text(status_x, 3, "TETRIS", "bold #7cff7c")
        self.grid.blit_text(status_x, 5, f"Score: {self.logic.score}", "#d6ffd6")
        self.grid.blit_text(status_x, 6, f"Lines: {self.logic.lines}", "#d6ffd6")
        self.grid.blit_text(status_x, 8, "Keys", "bold #7cff7c")
        self.grid.blit_text(status_x, 9, "<- -> move", "#b8fcb8")
        self.grid.blit_text(status_x, 10, "up/X rot", "#b8fcb8")
        self.grid.blit_text(status_x, 11, "down drop", "#b8fcb8")
        self.grid.blit_text(status_x, 12, "space hard", "#b8fcb8")
        self.grid.blit_text(status_x, 13, "R restart", "#b8fcb8")

        if self.logic.game_over:
            self.grid.blit_text(status_x, 15, "GAME OVER", "bold #ff8080")
            self.grid.blit_text(status_x, 16, "Press R", "#ffc0c0")
            message = " GAME OVER "
            self.grid.blit_text(
                well_x + ((rendered_well_width - len(message)) // 2),
                well_y + WELL_HEIGHT // 2,
                message,
                "bold #ff8080",
            )

    def _draw_box(self, x: int, y: int, width: int, height: int, style: str) -> None:
        x1 = x + width - 1
        y1 = y + height - 1
        self.grid.set_cell(x, y, "┏", style)
        self.grid.set_cell(x1, y, "┓", style)
        self.grid.set_cell(x, y1, "┗", style)
        self.grid.set_cell(x1, y1, "┛", style)
        for cx in range(x + 1, x1):
            self.grid.set_cell(cx, y, "━", style)
            self.grid.set_cell(cx, y1, "━", style)
        for cy in range(y + 1, y1):
            self.grid.set_cell(x, cy, "┃", style)
            self.grid.set_cell(x1, cy, "┃", style)
