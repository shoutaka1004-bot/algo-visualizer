from flask import Flask, jsonify, request, send_from_directory

from maze.generator import generate_maze
from maze.grid import Grid
from maze.solvers.astar import solve_astar
from maze.solvers.bfs import solve_bfs
from maze.solvers.dijkstra import solve_dijkstra
from sorting.bubble import sort_bubble
from sorting.merge import sort_merge
from sorting.quick import sort_quick

app = Flask(__name__, static_folder="../frontend", static_url_path="")


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


def _grid_to_walls(grid):
    """`Grid`を、行優先（yの昇順→xの昇順）の2次元真偽値配列に変換する。

    `grid[y][x]`が`True`なら壁、`False`なら通路。`Grid.__iter__`と同じ並び順
    にすることで、フロントエンドのCanvas描画（行ごとにループして塗る）と
    素直に対応させる。
    """
    return [
        [grid.get_cell(x, y).is_wall for x in range(grid.width)]
        for y in range(grid.height)
    ]


def _walls_to_grid(walls):
    """行優先の2次元真偽値配列（`grid[y][x]`、true=壁）から`Grid`を再構築する。

    `_grid_to_walls`の逆方向。寸法はリクエストの`width`/`height`フィールド
    ではなく`walls`自体の実寸（行数・先頭行の列数）から導出する。これにより
    `width`/`height`フィールドとの不整合チェックを省略できる（タスク16の
    担当範囲）。
    """
    height = len(walls)
    width = len(walls[0])
    grid = Grid(width, height)
    for y in range(height):
        for x in range(width):
            grid.get_cell(x, y).is_wall = walls[y][x]
    return grid


_SOLVERS = {
    "bfs": solve_bfs,
    "dijkstra": solve_dijkstra,
    "astar": solve_astar,
}

_SORTERS = {
    "bubble": sort_bubble,
    "quick": sort_quick,
    "merge": sort_merge,
}

_MAZE_SIZE_MIN = 3
_MAZE_SIZE_MAX = 101
_SORT_VALUES_MAX = 200


def _error(message):
    """400 + `{"error": message}` のレスポンスを組み立てる共通ヘルパー。

    3エンドポイント共通の「不正入力を平易な文言のJSONとして400で返す」
    という体裁だけをここに集約する。何を不正とみなすかの判定自体は、
    各エンドポイントの事情に合わせて個別に実装する（タスク16）。
    """
    return jsonify({"error": message}), 400


def _is_valid_maze_size(value):
    """`width`/`height`が3〜101の整数（bool型は除く）かどうかを判定する。

    JSONの`true`/`false`はPythonの`bool`（`int`のサブクラス）として渡って
    くるため、`isinstance(value, int)`だけでは`true`を1として通してしまう。
    そのため`bool`を明示的に除外する。小数（`float`）も、内部で`range()`に
    渡す都合上、整数以外は受け付けない。
    """
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and _MAZE_SIZE_MIN <= value <= _MAZE_SIZE_MAX
    )


def _is_valid_grid(grid):
    """`grid`が「1行以上・各行1列以上・全行同じ列数・全要素bool」かを判定する。"""
    if not isinstance(grid, list) or len(grid) == 0:
        return False
    if not isinstance(grid[0], list) or len(grid[0]) == 0:
        return False
    row_length = len(grid[0])
    for row in grid:
        if not isinstance(row, list) or len(row) != row_length:
            return False
        if not all(isinstance(cell, bool) for cell in row):
            return False
    return True


def _is_valid_sort_values(values):
    """`values`が「配列・全要素が数値（bool型は除く）」かを判定する（件数上限は別チェック）。"""
    return isinstance(values, list) and all(
        isinstance(v, (int, float)) and not isinstance(v, bool) for v in values
    )


@app.route("/api/maze", methods=["POST"])
def create_maze():
    """幅・高さを受け取り、生成した迷路とスタート/ゴール座標を返す。

    幅・高さは3〜101の整数であることを検証する（タスク16）。
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "リクエストボディが正しいJSON形式ではありません。"}), 400

    width = data.get("width")
    height = data.get("height")
    if not _is_valid_maze_size(width) or not _is_valid_maze_size(height):
        return _error("迷路の幅・高さ（width, height）は3〜101の整数で指定してください。")

    grid = generate_maze(width, height)

    return jsonify(
        {
            "width": grid.width,
            "height": grid.height,
            "grid": _grid_to_walls(grid),
            "start": {"x": 0, "y": 0},
            "goal": {"x": grid.width - 1, "y": grid.height - 1},
        }
    )


@app.route("/api/maze/solve", methods=["POST"])
def solve_maze():
    """迷路データとアルゴリズム名を受け取り、探索ステップ列を返す。

    リクエストボディは`/api/maze`のレスポンスと同じ形式の迷路データ
    （`grid`は必須。`width`/`height`は受け取っても`_walls_to_grid`が
    `grid`の実寸から独自に導出するため使わない）に、`algorithm`
    （`bfs`/`dijkstra`/`astar`のいずれか）を加えたもの。

    `algorithm`が既知の探索アルゴリズム名であること、`grid`が正しい形式の
    真偽値の2次元配列であることを検証する（タスク16）。
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "リクエストボディが正しいJSON形式ではありません。"}), 400

    algorithm = data.get("algorithm")
    if algorithm not in _SOLVERS:
        return _error(
            "探索アルゴリズムはbfs（幅優先探索）／dijkstra（ダイクストラ法）／"
            "astar（A*）のいずれかを指定してください。"
        )

    if not _is_valid_grid(data.get("grid")):
        return _error("迷路データの形式が正しくありません。迷路を生成し直してから探索してください。")

    grid = _walls_to_grid(data.get("grid"))
    solver = _SOLVERS[algorithm]

    start = (0, 0)
    goal = (grid.width - 1, grid.height - 1)
    steps = solver(grid, start, goal)

    return jsonify({"steps": steps})


@app.route("/api/sort", methods=["POST"])
def sort_values():
    """配列とアルゴリズム名を受け取り、ソートのステップ列を返す。

    リクエストボディは`{"values": [...], "algorithm": "bubble"}`形式
    （`algorithm`は`bubble`/`quick`/`merge`のいずれか）。

    `algorithm`が既知のソートアルゴリズム名であること、`values`が数値のみの
    配列であり件数が上限（200件）以内であることを検証する（タスク16）。
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "リクエストボディが正しいJSON形式ではありません。"}), 400

    algorithm = data.get("algorithm")
    if algorithm not in _SORTERS:
        return _error(
            "並び替えアルゴリズムはbubble（バブルソート）／quick（クイックソート）／"
            "merge（マージソート）のいずれかを指定してください。"
        )

    values = data.get("values")
    if not _is_valid_sort_values(values):
        return _error("並び替え対象の数値配列（values）が正しくありません。数値だけの配列を指定してください。")
    if len(values) > _SORT_VALUES_MAX:
        return _error("並び替えできる要素数は200個までです。もう少し少ない件数でお試しください。")

    sorter = _SORTERS[algorithm]
    steps = sorter(values)

    return jsonify({"steps": steps})


if __name__ == "__main__":
    app.run(port=5000)
