from random import Random

from workshop.games.tetris import Piece, TetrisLogic


def test_rotate_inside_well() -> None:
    logic = TetrisLogic(Random(0))
    logic.current = Piece(kind="T", rotation=0, x=3, y=0)

    rotated = logic.rotate()

    assert rotated
    assert logic.current.rotation == 1


def test_line_clear_updates_lines_and_score() -> None:
    logic = TetrisLogic(Random(0))
    logic.board[-1] = ["I" for _ in range(logic.width)]

    cleared = logic.clear_full_rows()
    logic.lines += cleared
    logic.score += [0, 100, 300, 500, 800][cleared]

    assert cleared == 1
    assert logic.lines == 1
    assert logic.score == 100
    assert all(cell is None for cell in logic.board[0])


def test_lock_piece_writes_to_board_and_spawns_next() -> None:
    logic = TetrisLogic(Random(0))
    logic.current = Piece(kind="O", rotation=0, x=3, y=logic.height - 2)

    logic.soft_drop()

    occupied = sum(1 for row in logic.board for cell in row if cell is not None)
    assert occupied >= 4
    assert logic.current.kind in {"I", "J", "L", "O", "S", "T", "Z"}


def test_game_over_when_spawn_is_blocked() -> None:
    logic = TetrisLogic(Random(0))
    for y in range(4):
        for x in range(logic.width):
            logic.board[y][x] = "I"

    logic.current = logic._spawn_piece()

    assert logic.game_over
