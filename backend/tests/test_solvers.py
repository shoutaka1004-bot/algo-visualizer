import random

from maze.generator import generate_maze
from maze.grid import Grid
from maze.solvers.astar import solve_astar
from maze.solvers.bfs import solve_bfs
from maze.solvers.dijkstra import solve_dijkstra


def _open(grid, cells):
    """`cells`（`(x, y)`のイテラブル）を通路（`is_wall = False`）にする。"""
    for x, y in cells:
        grid.get_cell(x, y).is_wall = False


def _detour_grid():
    """スタートからゴールまでの直線（行0）を壁で塞ぎ、行1経由の迂回路
    のみを通路にした5x5グリッド。行2に繋がらない行き止まり枝も1つ足す。

    最短経路は (0,0)-(0,1)-(1,1)-(2,1)-(3,1)-(4,1)-(4,0) の7マスになる。
    """
    grid = Grid(5, 5)
    _open(
        grid,
        [
            (0, 0),
            (0, 1),
            (1, 1),
            (2, 1),
            (3, 1),
            (4, 1),
            (4, 0),
            (2, 2),  # (2, 1)から伸びるだけの行き止まり
        ],
    )
    return grid


def _path_step(steps):
    path_steps = [s for s in steps if s["type"] == "path"]
    assert len(path_steps) <= 1
    return path_steps[0] if path_steps else None


def test_solve_bfs_finds_shortest_path_around_walls():
    grid = _detour_grid()
    steps = solve_bfs(grid, (0, 0), (4, 0))

    path_step = _path_step(steps)
    assert path_step is not None
    assert path_step["cells"] == [
        [0, 0],
        [0, 1],
        [1, 1],
        [2, 1],
        [3, 1],
        [4, 1],
        [4, 0],
    ]


def test_solve_bfs_visits_dead_end_but_excludes_it_from_path():
    grid = _detour_grid()
    steps = solve_bfs(grid, (0, 0), (4, 0))

    visited_cells = {(s["x"], s["y"]) for s in steps if s["type"] == "visit"}
    assert (2, 2) in visited_cells

    path_step = _path_step(steps)
    assert [2, 2] not in path_step["cells"]


def test_solve_bfs_does_not_traverse_walls():
    grid = _detour_grid()
    steps = solve_bfs(grid, (0, 0), (4, 0))

    visited_cells = {(s["x"], s["y"]) for s in steps if s["type"] == "visit"}
    # (1, 0)は行0上にあり壁のまま残しているセルの一つ。
    assert (1, 0) not in visited_cells


def test_solve_bfs_returns_no_path_step_when_unreachable():
    grid = Grid(3, 3)
    _open(grid, [(0, 0), (2, 2)])  # 互いに繋がっていない孤立した通路

    steps = solve_bfs(grid, (0, 0), (2, 2))

    assert _path_step(steps) is None
    visit_cells = [(s["x"], s["y"]) for s in steps if s["type"] == "visit"]
    assert visit_cells == [(0, 0)]


def test_solve_bfs_on_generated_maze_returns_valid_shortest_path():
    grid = generate_maze(11, 11, rng=random.Random(42))
    start = (0, 0)
    goal = (grid.width - 1, grid.height - 1)

    steps = solve_bfs(grid, start, goal)
    path_step = _path_step(steps)

    assert path_step is not None
    cells = path_step["cells"]
    assert cells[0] == list(start)
    assert cells[-1] == list(goal)

    # 経路上の全セルが通路であり、隣接セル同士が4方向で1マスずつ
    # 繋がっていることを確認する。
    for x, y in cells:
        assert grid.get_cell(x, y).is_wall is False
    for (x1, y1), (x2, y2) in zip(cells, cells[1:]):
        assert abs(x1 - x2) + abs(y1 - y2) == 1


def test_solve_bfs_start_equals_goal_returns_single_cell_path():
    grid = Grid(3, 3)
    _open(grid, [(1, 1)])

    steps = solve_bfs(grid, (1, 1), (1, 1))

    path_step = _path_step(steps)
    assert path_step is not None
    assert path_step["cells"] == [[1, 1]]


def test_solve_dijkstra_finds_shortest_path_around_walls():
    grid = _detour_grid()
    steps = solve_dijkstra(grid, (0, 0), (4, 0))

    path_step = _path_step(steps)
    assert path_step is not None
    assert path_step["cells"] == [
        [0, 0],
        [0, 1],
        [1, 1],
        [2, 1],
        [3, 1],
        [4, 1],
        [4, 0],
    ]


def test_solve_dijkstra_visits_dead_end_but_excludes_it_from_path():
    grid = _detour_grid()
    steps = solve_dijkstra(grid, (0, 0), (4, 0))

    visited_cells = {(s["x"], s["y"]) for s in steps if s["type"] == "visit"}
    assert (2, 2) in visited_cells

    path_step = _path_step(steps)
    assert [2, 2] not in path_step["cells"]


def test_solve_dijkstra_does_not_traverse_walls():
    grid = _detour_grid()
    steps = solve_dijkstra(grid, (0, 0), (4, 0))

    visited_cells = {(s["x"], s["y"]) for s in steps if s["type"] == "visit"}
    # (1, 0)は行0上にあり壁のまま残しているセルの一つ。
    assert (1, 0) not in visited_cells


def test_solve_dijkstra_returns_no_path_step_when_unreachable():
    grid = Grid(3, 3)
    _open(grid, [(0, 0), (2, 2)])  # 互いに繋がっていない孤立した通路

    steps = solve_dijkstra(grid, (0, 0), (2, 2))

    assert _path_step(steps) is None
    visit_cells = [(s["x"], s["y"]) for s in steps if s["type"] == "visit"]
    assert visit_cells == [(0, 0)]


def test_solve_dijkstra_on_generated_maze_returns_valid_shortest_path():
    grid = generate_maze(11, 11, rng=random.Random(42))
    start = (0, 0)
    goal = (grid.width - 1, grid.height - 1)

    steps = solve_dijkstra(grid, start, goal)
    path_step = _path_step(steps)

    assert path_step is not None
    cells = path_step["cells"]
    assert cells[0] == list(start)
    assert cells[-1] == list(goal)

    # 経路上の全セルが通路であり、隣接セル同士が4方向で1マスずつ
    # 繋がっていることを確認する。
    for x, y in cells:
        assert grid.get_cell(x, y).is_wall is False
    for (x1, y1), (x2, y2) in zip(cells, cells[1:]):
        assert abs(x1 - x2) + abs(y1 - y2) == 1


def test_solve_dijkstra_start_equals_goal_returns_single_cell_path():
    grid = Grid(3, 3)
    _open(grid, [(1, 1)])

    steps = solve_dijkstra(grid, (1, 1), (1, 1))

    path_step = _path_step(steps)
    assert path_step is not None
    assert path_step["cells"] == [[1, 1]]


def test_solve_dijkstra_matches_bfs_shortest_path_length_on_generated_maze():
    """コストが全て1の重み無しグリッドでは、Dijkstra法もBFSと同じ
    最短経路長になるはず（優先度付きキューを使う実装であること自体が
    今回のタスクの目的であり、経路長そのものはBFSと一致する）。"""
    grid = generate_maze(15, 15, rng=random.Random(7))
    start = (0, 0)
    goal = (grid.width - 1, grid.height - 1)

    bfs_path = _path_step(solve_bfs(grid, start, goal))
    dijkstra_path = _path_step(solve_dijkstra(grid, start, goal))

    assert bfs_path is not None
    assert dijkstra_path is not None
    assert len(bfs_path["cells"]) == len(dijkstra_path["cells"])


def test_solve_astar_finds_shortest_path_around_walls():
    grid = _detour_grid()
    steps = solve_astar(grid, (0, 0), (4, 0))

    path_step = _path_step(steps)
    assert path_step is not None
    assert path_step["cells"] == [
        [0, 0],
        [0, 1],
        [1, 1],
        [2, 1],
        [3, 1],
        [4, 1],
        [4, 0],
    ]


def test_solve_astar_prunes_dead_end_thanks_to_heuristic():
    """BFS/Dijkstra法は行き止まり(2, 2)を訪問してから最短経路を確定するが、
    A*はマンハッタン距離ヒューリスティックにより(2, 2)方向のf値が本経路上の
    どのセルのf値よりも常に大きくなるため、ゴールに到達するまで(2, 2)を
    一度も訪問しない（これはバグではなくA*の枝刈り効果そのものであり、
    BFS/Dijkstra用のテストをそのまま流用できない点に注意）。いずれにせよ
    最短経路には含まれないことを確認する。"""
    grid = _detour_grid()
    steps = solve_astar(grid, (0, 0), (4, 0))

    visited_cells = {(s["x"], s["y"]) for s in steps if s["type"] == "visit"}
    assert (2, 2) not in visited_cells

    path_step = _path_step(steps)
    assert [2, 2] not in path_step["cells"]


def test_solve_astar_does_not_traverse_walls():
    grid = _detour_grid()
    steps = solve_astar(grid, (0, 0), (4, 0))

    visited_cells = {(s["x"], s["y"]) for s in steps if s["type"] == "visit"}
    # (1, 0)は行0上にあり壁のまま残しているセルの一つ。
    assert (1, 0) not in visited_cells


def test_solve_astar_returns_no_path_step_when_unreachable():
    grid = Grid(3, 3)
    _open(grid, [(0, 0), (2, 2)])  # 互いに繋がっていない孤立した通路

    steps = solve_astar(grid, (0, 0), (2, 2))

    assert _path_step(steps) is None
    visit_cells = [(s["x"], s["y"]) for s in steps if s["type"] == "visit"]
    assert visit_cells == [(0, 0)]


def test_solve_astar_on_generated_maze_returns_valid_shortest_path():
    grid = generate_maze(11, 11, rng=random.Random(42))
    start = (0, 0)
    goal = (grid.width - 1, grid.height - 1)

    steps = solve_astar(grid, start, goal)
    path_step = _path_step(steps)

    assert path_step is not None
    cells = path_step["cells"]
    assert cells[0] == list(start)
    assert cells[-1] == list(goal)

    # 経路上の全セルが通路であり、隣接セル同士が4方向で1マスずつ
    # 繋がっていることを確認する。
    for x, y in cells:
        assert grid.get_cell(x, y).is_wall is False
    for (x1, y1), (x2, y2) in zip(cells, cells[1:]):
        assert abs(x1 - x2) + abs(y1 - y2) == 1


def test_solve_astar_start_equals_goal_returns_single_cell_path():
    grid = Grid(3, 3)
    _open(grid, [(1, 1)])

    steps = solve_astar(grid, (1, 1), (1, 1))

    path_step = _path_step(steps)
    assert path_step is not None
    assert path_step["cells"] == [[1, 1]]


def test_solve_astar_matches_bfs_and_dijkstra_shortest_path_length_on_generated_maze():
    """マンハッタン距離ヒューリスティックは4方向移動・コスト1の迷路では
    許容的（admissible）なため、A*もBFS・Dijkstra法と同じ最短経路長になる
    はず（優先度付きキュー＋ヒューリスティックを使う実装であること自体が
    今回のタスクの目的であり、経路長そのものは両者と一致する）。"""
    grid = generate_maze(15, 15, rng=random.Random(7))
    start = (0, 0)
    goal = (grid.width - 1, grid.height - 1)

    bfs_path = _path_step(solve_bfs(grid, start, goal))
    dijkstra_path = _path_step(solve_dijkstra(grid, start, goal))
    astar_path = _path_step(solve_astar(grid, start, goal))

    assert bfs_path is not None
    assert dijkstra_path is not None
    assert astar_path is not None
    assert len(bfs_path["cells"]) == len(dijkstra_path["cells"]) == len(astar_path["cells"])
