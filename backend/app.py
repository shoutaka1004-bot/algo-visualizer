from flask import Flask, jsonify, request, send_from_directory

from maze.generator import generate_maze

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


if __name__ == "__main__":
    app.run(port=5000)
