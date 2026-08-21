from random import Random

from workshop.games.pong import PongLogic


def test_ball_bounces_off_top_and_bottom() -> None:
    logic = PongLogic(40, 16, Random(0))

    logic.ball_y = 0.0
    logic.ball_vy = -0.4
    logic.step()
    assert logic.ball_vy > 0

    logic.ball_y = float(logic.height - 1)
    logic.ball_vy = 0.4
    logic.step()
    assert logic.ball_vy < 0


def test_score_when_ball_passes_side() -> None:
    logic = PongLogic(40, 16, Random(0))

    logic.ball_x = -1.0
    logic.ball_vx = -1.0
    logic.ball_y = logic.height - 1.0
    logic.step()

    assert logic.right_score == 1


def test_paddle_clamping() -> None:
    logic = PongLogic(40, 16, Random(0))

    logic.move_left(-100)
    logic.move_right(100)

    assert logic.left_y == 0.0
    assert logic.right_y == float(logic.height - logic.paddle_size)


def test_win_at_five_freezes_match() -> None:
    logic = PongLogic(40, 16, Random(0))
    logic.left_score = 4
    logic.ball_x = logic.width
    logic.ball_vx = 1.0
    logic.ball_y = 0.0

    logic.step()

    assert logic.left_score == 5
    assert logic.winner == "LEFT"

    prev_x = logic.ball_x
    logic.step()
    assert logic.ball_x == prev_x
