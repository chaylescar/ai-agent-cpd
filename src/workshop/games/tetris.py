"""Tetris game screen and pure logic helpers for workshop tests."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Literal

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


@dataclass
class CpuController:
    target_x: int = 0
    target_rotation: int = 0
    piece_id: int | None = None


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


def _column_heights(board: Board) -> list[int]:
    width = len(board[0]) if board else 0
    height = len(board)
    heights: list[int] = []
    for x in range(width):
        col_height = 0
        for y in range(height):
            if board[y][x] is not None:
                col_height = height - y
                break
        heights.append(col_height)
    return heights


def _count_holes(board: Board) -> int:
    width = len(board[0]) if board else 0
    height = len(board)
    holes = 0
    for x in range(width):
        seen_block = False
        for y in range(height):
            if board[y][x] is not None:
                seen_block = True
            elif seen_block:
                holes += 1
    return holes


def _board_score(board: Board, lines_cleared: int) -> int:
    heights = _column_heights(board)
    holes = _count_holes(board)
    bumpiness = sum(abs(heights[i] - heights[i + 1]) for i in range(len(heights) - 1))
    aggregate_height = sum(heights)
    return (lines_cleared * 1000) - (holes * 40) - (bumpiness * 6) - (aggregate_height * 3)


def _choose_cpu_target(logic: TetrisLogic) -> tuple[int, int]:
    if logic.current is None:
        return (0, 0)

    width = len(logic.board[0]) if logic.board else WELL_WIDTH
    best_score: int | None = None
    best_target = (logic.current.x, logic.current.rotation)

    for rotation in range(4):
        for x in range(-2, width + 2):
            candidate = Piece(logic.current.kind, x, logic.current.y, rotation)
            if not can_place(logic.board, candidate):
                continue

            dropped = Piece(candidate.kind, candidate.x, candidate.y, candidate.rotation)
            while try_move(logic.board, dropped, 0, 1):
                pass

            simulated = [row[:] for row in logic.board]
            lock_piece(simulated, dropped)
            cleared = clear_full_rows(simulated)
            score = _board_score(simulated, cleared)
            if best_score is None or score > best_score:
                best_score = score
                best_target = (x, rotation)

    return best_target


def apply_cpu_step(logic: TetrisLogic, cpu: CpuController) -> None:
    if logic.game_over or logic.current is None:
        return

    current_id = id(logic.current)
    if cpu.piece_id != current_id:
        cpu.piece_id = current_id
        cpu.target_x, cpu.target_rotation = _choose_cpu_target(logic)

    if logic.current.rotation != cpu.target_rotation:
        logic.rotate()
        return

    if logic.current.x < cpu.target_x:
        logic.move_right()
        return

    if logic.current.x > cpu.target_x:
        logic.move_left()
        return

    logic.soft_drop()


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
        self.mode: Literal["select", "single", "multi", "vs_cpu"] = "select"
        self.logic = TetrisLogic()
        self.logic_p1 = TetrisLogic()
        self.logic_p2 = TetrisLogic()
        self.cpu_p2 = CpuController()
        self._draw_game()

    def on_tick(self) -> None:
        if self.mode == "single":
            self.logic.tick()
        elif self.mode == "multi":
            self.logic_p1.tick()
            self.logic_p2.tick()
        elif self.mode == "vs_cpu":
            apply_cpu_step(self.logic_p2, self.cpu_p2)
            self.logic_p1.tick()
            self.logic_p2.tick()
        self._draw_game()

    def on_game_key(self, key: str) -> None:
        if self.mode == "select":
            if key == "1":
                self.mode = "single"
                self.logic.restart()
            elif key == "2":
                self.mode = "multi"
                self.logic_p1.restart()
                self.logic_p2.restart()
            elif key == "3":
                self.mode = "vs_cpu"
                self.logic_p1.restart()
                self.logic_p2.restart()
                self.cpu_p2 = CpuController()
            self._draw_game()
            return

        if key == "r":
            if self.mode == "single":
                self.logic.restart()
            elif self.mode == "multi":
                self.logic_p1.restart()
                self.logic_p2.restart()
            elif self.mode == "vs_cpu":
                self.logic_p1.restart()
                self.logic_p2.restart()
                self.cpu_p2 = CpuController()
            self._draw_game()
            return

        if self.mode == "single":
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
        elif self.mode == "multi":
            if key == "a" and not self.logic_p1.game_over:
                self.logic_p1.move_left()
            elif key == "d" and not self.logic_p1.game_over:
                self.logic_p1.move_right()
            elif key == "w" and not self.logic_p1.game_over:
                self.logic_p1.rotate()
            elif key == "s" and not self.logic_p1.game_over:
                self.logic_p1.soft_drop()
            elif key == "f" and not self.logic_p1.game_over:
                self.logic_p1.hard_drop()
            elif key == "left" and not self.logic_p2.game_over:
                self.logic_p2.move_left()
            elif key == "right" and not self.logic_p2.game_over:
                self.logic_p2.move_right()
            elif key in {"up", "x"} and not self.logic_p2.game_over:
                self.logic_p2.rotate()
            elif key == "down" and not self.logic_p2.game_over:
                self.logic_p2.soft_drop()
            elif key == "space" and not self.logic_p2.game_over:
                self.logic_p2.hard_drop()
        elif self.mode == "vs_cpu":
            if self.logic_p1.game_over:
                self._draw_game()
                return
            if key in {"a", "left"}:
                self.logic_p1.move_left()
            elif key in {"d", "right"}:
                self.logic_p1.move_right()
            elif key in {"w", "up", "x"}:
                self.logic_p1.rotate()
            elif key in {"s", "down"}:
                self.logic_p1.soft_drop()
            elif key in {"f", "space"}:
                self.logic_p1.hard_drop()

        self._draw_game()

    def _draw_game(self) -> None:
        if self.mode == "select":
            self._draw_mode_select()
            return
        if self.mode == "single":
            self._draw_single_player()
            return
        if self.mode == "multi":
            self._draw_multiplayer()
            return
        self._draw_vs_cpu()

    def _draw_mode_select(self) -> None:
        self.grid.clear(" ", "#031403")
        self.grid.draw_border(style="bold #33ff33")
        self.grid.blit_text(19, 4, "TETRIS", "bold #7cff7c")
        self.grid.blit_text(12, 7, "Select mode", "bold #d6ffd6")
        self.grid.blit_text(12, 10, "1  Single Player", "#b8fcb8")
        self.grid.blit_text(12, 12, "2  Local Multiplayer", "#b8fcb8")
        self.grid.blit_text(12, 14, "3  VS CPU", "#b8fcb8")
        self.grid.blit_text(12, 17, "Q / Esc back to menu", "#9fe99f")

    def _draw_single_player(self) -> None:
        self.grid.clear(" ", "#031403")
        self.grid.draw_border(style="bold #33ff33")

        well_x = 3
        well_y = 2
        rendered_well_width = (WELL_WIDTH * CELL_WIDTH) + 2
        self._draw_box(well_x, well_y, rendered_well_width, WELL_HEIGHT + 2, "bold #33ff33")

        self._draw_logic_board(self.logic, well_x, well_y)

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

    def _draw_multiplayer(self) -> None:
        self.grid.clear(" ", "#031403")
        left_well_x = 1
        right_well_x = 24
        well_y = 0
        rendered_well_width = (WELL_WIDTH * CELL_WIDTH) + 2
        winner_banner = self._multiplayer_winner_banner(self.logic_p1, self.logic_p2, "P1", "P2")

        self._draw_box(left_well_x, well_y, rendered_well_width, WELL_HEIGHT + 2, "bold #33ff33")
        self._draw_box(right_well_x, well_y, rendered_well_width, WELL_HEIGHT + 2, "bold #33ff33")
        self._draw_logic_board(self.logic_p1, left_well_x, well_y)
        self._draw_logic_board(self.logic_p2, right_well_x, well_y)

        if winner_banner is None:
            self.grid.blit_text(
                left_well_x + 1,
                22,
                f"P1 S:{self.logic_p1.score} L:{self.logic_p1.lines}",
                "#d6ffd6",
            )
            self.grid.blit_text(
                right_well_x + 1,
                22,
                f"P2 S:{self.logic_p2.score} L:{self.logic_p2.lines}",
                "#d6ffd6",
            )
        else:
            banner_x = (self.COLS - len(winner_banner)) // 2
            self.grid.blit_text(banner_x, 22, winner_banner, "bold #ffd166")

        if self.logic_p1.game_over:
            self.grid.blit_text(left_well_x + 5, 11, " GAME OVER ", "bold #ff8080")
        if self.logic_p2.game_over:
            self.grid.blit_text(right_well_x + 5, 11, " GAME OVER ", "bold #ff8080")

        self.grid.blit_text(
            1,
            23,
            "P1 A/D/W/S/F   P2 arrows/up/down/x/space   R restart",
            "#9fe99f",
        )

    def _draw_vs_cpu(self) -> None:
        self.grid.clear(" ", "#031403")
        left_well_x = 1
        right_well_x = 24
        well_y = 0
        rendered_well_width = (WELL_WIDTH * CELL_WIDTH) + 2

        self._draw_box(left_well_x, well_y, rendered_well_width, WELL_HEIGHT + 2, "bold #33ff33")
        self._draw_box(right_well_x, well_y, rendered_well_width, WELL_HEIGHT + 2, "bold #33ff33")
        self._draw_logic_board(self.logic_p1, left_well_x, well_y)
        self._draw_logic_board(self.logic_p2, right_well_x, well_y)

        self.grid.blit_text(
            left_well_x + 1,
            22,
            f"YOU S:{self.logic_p1.score} L:{self.logic_p1.lines}",
            "#d6ffd6",
        )
        self.grid.blit_text(
            right_well_x + 1,
            22,
            f"CPU S:{self.logic_p2.score} L:{self.logic_p2.lines}",
            "#d6ffd6",
        )

        if self.logic_p1.game_over:
            self.grid.blit_text(left_well_x + 5, 11, " GAME OVER ", "bold #ff8080")
        if self.logic_p2.game_over:
            self.grid.blit_text(right_well_x + 5, 11, " GAME OVER ", "bold #ff8080")

        winner_banner = self._multiplayer_winner_banner(self.logic_p1, self.logic_p2, "YOU", "CPU")
        if winner_banner is not None:
            banner_x = (self.COLS - len(winner_banner)) // 2
            self.grid.blit_text(banner_x, 21, winner_banner, "bold #ffd166")

        self.grid.blit_text(
            1,
            23,
            "YOU A/D/W/S/F or arrows   CPU auto   R restart",
            "#9fe99f",
        )

    def _multiplayer_winner_banner(
        self,
        left_logic: TetrisLogic,
        right_logic: TetrisLogic,
        left_name: str,
        right_name: str,
    ) -> str | None:
        p1_dead = left_logic.game_over
        p2_dead = right_logic.game_over
        if not p1_dead and not p2_dead:
            return None
        if p1_dead and not p2_dead:
            return f"{right_name} WINS"
        if p2_dead and not p1_dead:
            return f"{left_name} WINS"
        if left_logic.score > right_logic.score:
            return f"{left_name} WINS"
        if right_logic.score > left_logic.score:
            return f"{right_name} WINS"
        return "DRAW"

    def _draw_logic_board(self, logic: TetrisLogic, well_x: int, well_y: int) -> None:
        for y, row in enumerate(logic.board):
            for x, cell in enumerate(row):
                if cell is None:
                    continue
                self.grid.blit_text(
                    well_x + 1 + (x * CELL_WIDTH),
                    well_y + 1 + y,
                    BLOCK_GLYPH,
                    f"bold {PIECE_COLORS[cell]}",
                )

        if logic.current is not None:
            for x, y in piece_cells(logic.current):
                self.grid.blit_text(
                    well_x + 1 + (x * CELL_WIDTH),
                    well_y + 1 + y,
                    BLOCK_GLYPH,
                    f"bold {PIECE_COLORS[logic.current.kind]}",
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
