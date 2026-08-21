from __future__ import annotations

from random import Random

from workshop.games.tetris import (
    Piece,
    TetrisLogic,
    can_place,
    clear_full_rows,
    empty_board,
    lock_piece,
    try_rotate,
)


def test_rotate_inside_well() -> None:
    board = empty_board()
    piece = Piece(kind="T", x=3, y=3, rotation=0)

    assert can_place(board, piece)
    assert try_rotate(board, piece)
    assert piece.rotation == 1
    assert can_place(board, piece)


def test_clear_full_rows_compacts_board() -> None:
    board = empty_board()
    board[-1] = ["I" for _ in range(10)]
    board[-2][0] = "O"

    cleared = clear_full_rows(board)

    assert cleared == 1
    assert board[0] == [None for _ in range(10)]
    assert board[-1][0] == "O"


def test_lock_places_piece_blocks() -> None:
    board = empty_board()
    piece = Piece(kind="O", x=3, y=4, rotation=0)

    lock_piece(board, piece)

    assert board[4][4] == "O"
    assert board[4][5] == "O"
    assert board[5][4] == "O"
    assert board[5][5] == "O"


def test_game_over_when_spawn_is_blocked() -> None:
    logic = TetrisLogic(rng=Random(0))
    logic.board = empty_board()
    logic.current = Piece(kind="O", x=3, y=18, rotation=0)

    logic.board[1][4] = "Z"

    logic.tick()

    assert logic.game_over
    assert logic.current is None
