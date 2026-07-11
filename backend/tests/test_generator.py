import random

import pytest

from maze.generator import generate_maze


def _passage_cells(grid):
    return {(cell.x, cell.y) for cell in grid if not cell.is_wall}


def _reachable_from(grid, start):
    """スタートから4方向のみで到達できる通路セルの集合を返す簡易フラッドフィル。

    将来のsolvers（BFS等）には依存しない、このテスト専用の独立実装。
    """
    visited = {start}
    stack = [start]
    while stack:
        x, y = stack.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not grid.in_bounds(nx, ny):
                continue
            if (nx, ny) in visited:
                continue
            if grid.get_cell(nx, ny).is_wall:
                continue
            visited.add((nx, ny))
            stack.append((nx, ny))
    return visited


@pytest.mark.parametrize("width, height", [(5, 5), (7, 9), (3, 3), (15, 5)])
def test_odd_dimensions_generate_as_requested(width, height):
    grid = generate_maze(width, height, rng=random.Random(0))
    assert grid.width == width
    assert grid.height == height


@pytest.mark.parametrize(
    "width, height, expected_width, expected_height",
    [(10, 10, 9, 9), (10, 9, 9, 9), (9, 10, 9, 9), (4, 6, 3, 5)],
)
def test_even_dimensions_are_adjusted_to_nearest_odd(
    width, height, expected_width, expected_height
):
    grid = generate_maze(width, height, rng=random.Random(0))
    assert grid.width == expected_width
    assert grid.height == expected_height


@pytest.mark.parametrize("width, height", [(1, 5), (2, 5), (5, 1), (5, 2), (0, 0)])
def test_dimensions_below_three_raise_value_error(width, height):
    with pytest.raises(ValueError):
        generate_maze(width, height)


@pytest.mark.parametrize("width, height", [(5, 5), (7, 9), (15, 15), (25, 25)])
def test_start_and_goal_are_passages(width, height):
    grid = generate_maze(width, height, rng=random.Random(1))
    start = (0, 0)
    goal = (grid.width - 1, grid.height - 1)
    assert grid.get_cell(*start).is_wall is False
    assert grid.get_cell(*goal).is_wall is False


@pytest.mark.parametrize("width, height", [(5, 5), (7, 9), (15, 15), (25, 25)])
def test_all_passage_cells_are_connected(width, height):
    grid = generate_maze(width, height, rng=random.Random(2))
    all_passages = _passage_cells(grid)
    reachable = _reachable_from(grid, (0, 0))
    assert reachable == all_passages


def test_goal_reachable_from_start():
    grid = generate_maze(11, 11, rng=random.Random(3))
    goal = (grid.width - 1, grid.height - 1)
    reachable = _reachable_from(grid, (0, 0))
    assert goal in reachable


def test_generation_is_deterministic_with_same_seed():
    grid_a = generate_maze(9, 9, rng=random.Random(42))
    grid_b = generate_maze(9, 9, rng=random.Random(42))
    assert _passage_cells(grid_a) == _passage_cells(grid_b)


def _render_ascii(grid):
    """デバッグ用にGridをASCIIアート（'.'=通路, '#'=壁）へ変換する。"""
    lines = []
    for y in range(grid.height):
        row = "".join(
            "." if not grid.get_cell(x, y).is_wall else "#"
            for x in range(grid.width)
        )
        lines.append(row)
    return "\n".join(lines)


@pytest.mark.parametrize("width, height", [(5, 5), (7, 9), (9, 9), (15, 15), (25, 25)])
def test_border_is_walled_except_entrance_and_exit(width, height):
    """外周（角の入口・出口セルを除く）が壁で囲まれていることを確認する。

    穴掘り法の「部屋」が外周セルまで含んでしまうと、外周に壁が残らず
    迷路として視覚的に破綻する（実案件レビューで発見された不具合）。
    ASCIIアートで可視化しても目視確認できるよう、失敗時のメッセージに
    アートを含める。
    """
    grid = generate_maze(width, height, rng=random.Random(7))
    w, h = grid.width, grid.height

    # 入口(スタート側)・出口(ゴール側)としてのみ穴が開くことを許容する2セルずつ。
    allowed_openings = {
        (0, 0),
        (1, 0),
        (w - 2, h - 1),
        (w - 1, h - 1),
    }

    border_cells = set()
    for x in range(w):
        border_cells.add((x, 0))
        border_cells.add((x, h - 1))
    for y in range(h):
        border_cells.add((0, y))
        border_cells.add((w - 1, y))

    ascii_art = _render_ascii(grid)

    for x, y in border_cells:
        if (x, y) in allowed_openings:
            continue
        assert grid.get_cell(x, y).is_wall is True, (
            f"border cell ({x}, {y}) should remain a wall but is a passage.\n"
            f"maze ({w}x{h}):\n{ascii_art}"
        )
