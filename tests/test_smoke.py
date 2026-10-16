import asyncio

from workshop import __version__
from workshop.app import ArcadeApp
from workshop.game import GameScreen
from workshop.games import GAMES, load_game_screen
from workshop.grid import CellGrid
from workshop.playfield import Playfield


def test_version() -> None:
    assert __version__


def test_set_cell_and_clip() -> None:
    grid = CellGrid(8, 6)
    grid.set_cell(2, 3, "A", "red")
    assert grid.get_char(2, 3) == "A"
    grid.set_cell(-1, 0, "X")
    grid.set_cell(80, 80, "X")
    assert grid.get_char(0, 0) == " "


def test_fill_rect_and_text() -> None:
    grid = CellGrid(10, 6)
    grid.fill_rect(1, 1, 3, 2, "█", "cyan")
    assert grid.get_char(1, 1) == "█"
    assert grid.get_char(3, 2) == "█"
    assert grid.get_char(4, 1) == " "
    grid.blit_text(0, 5, "HI")
    assert grid.get_char(0, 5) == "H"
    assert grid.get_char(1, 5) == "I"


def test_border() -> None:
    grid = CellGrid(8, 6)
    grid.draw_border()
    assert grid.get_char(0, 0) == "┏"
    assert grid.get_char(7, 5) == "┛"
    assert grid.get_char(1, 0) == "━"


def test_as_rich_text_contains_drawn_glyphs() -> None:
    grid = CellGrid(5, 3)
    grid.blit_text(0, 1, "Go")
    assert "Go" in grid.as_rich_text().plain


def test_catalogue_unbuilt() -> None:
    assert [spec.slug for spec in GAMES] == ["snake", "pong", "tetris"]
    assert load_game_screen("snake") is not None
    assert load_game_screen("pong") is None
    assert load_game_screen("tetris") is None


def test_arcade_menu_headless() -> None:
    async def scenario() -> None:
        app = ArcadeApp()
        async with app.run_test(size=(80, 32), notifications=True) as pilot:
            await pilot.pause()
            menu = str(app.query_one("#menu").content)
            assert "SNAKE" in menu
            assert "PONG" in menu
            assert "TETRIS" in menu
            assert "NOT BUILT" in menu
            await pilot.press("down")
            await pilot.pause()
            assert app.cursor == 1
            await pilot.press("enter")
            await pilot.pause()

    asyncio.run(scenario())


class _DummyGame(GameScreen):
    TITLE = "DUMMY"
    COLS = 16
    ROWS = 10
    TICK_HZ = 8

    def on_start(self) -> None:
        self.grid.draw_border()
        self.grid.blit_text(2, 2, "OK", "green")


def test_game_screen_headless() -> None:
    async def scenario() -> None:
        app = ArcadeApp()
        async with app.run_test(size=(80, 32)) as pilot:
            await pilot.pause()
            await app.push_screen(_DummyGame())
            await pilot.pause()
            playfield = app.screen.query_one("#playfield", Playfield)
            assert playfield.grid.get_char(2, 2) == "O"
            await pilot.press("q")
            await pilot.pause()
            assert "SNAKE" in str(app.query_one("#menu").content)

    asyncio.run(scenario())
