from flask import Flask, jsonify, request, send_from_directory

from maze.generator import generate_maze
from maze.grid import Grid
from maze.solvers.astar import solve_astar
from maze.solvers.bfs import solve_bfs
from maze.solvers.dijkstra import solve_dijkstra

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


@app.route("/api/maze", methods=["POST"])
def create_maze():
    """幅・高さを受け取り、生成した迷路とスタート/ゴール座標を返す。

    幅・高さの欠損・型不正・範囲外チェックはタスク16の担当範囲のため、
    ここではリクエストボディがJSONとして解釈できない場合のみ400を返す
    （明らかにクラッシュする入力への最低限の防御）。
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "リクエストボディが正しいJSON形式ではありません。"}), 400

    grid = generate_maze(data.get("width"), data.get("height"))

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

    存在しないアルゴリズム名・`grid`欠損などの丁寧なバリデーションは
    タスク16の担当範囲のため、ここではリクエストボディがJSONとして
    解釈できない場合のみ400を返す（明らかにクラッシュする入力への
    最低限の防御）。
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "リクエストボディが正しいJSON形式ではありません。"}), 400

    grid = _walls_to_grid(data.get("grid"))
    solver = _SOLVERS[data.get("algorithm")]

    start = (0, 0)
    goal = (grid.width - 1, grid.height - 1)
    steps = solver(grid, start, goal)

    return jsonify({"steps": steps})


if __name__ == "__main__":
    app.run(port=5000)
