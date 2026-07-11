"""迷路生成アルゴリズム（穴掘り法／recursive backtracker）。

`Grid`/`Cell`はセル単体が壁かどうかしか表現できない（壁を独立した区画として
持たない）ため、素朴に隣接セルを1マスずつ掘ると全セルが連結してしまい壁が
一切残らず、迷路として成立しない。そのため、このモジュールでは以下の
「二重解像度」の考え方を採用する。

- 座標が偶数(x, y)のセルを「部屋」とする。
- 部屋から2マス離れた隣の部屋へ進む際、その間（1マス先）の壁も同時に
  取り払うことで、部屋同士をつなぐ通路を作る。
- 全ての部屋を訪問し終えると、通路セル全体が単一の全域木（スパニング
  ツリー）になり、通路同士は構造上必ず連結する。

この方式は「部屋」が偶数座標にしか存在できないため、内部的には
width・heightが共に奇数であることを前提に生成する。
"""

import random


from .grid import Grid


def generate_maze(width, height, rng=None):
    """穴掘り法（recursive backtracker）で迷路を生成する。

    `width`・`height`が偶数の場合、部屋（偶数座標のセル）の格子に収まる
    よう内部で1減らし、直近の奇数に自動調整してから生成する
    （例: width=10 → 実際には9で生成する）。返り値の`Grid`は、この
    調整後の実サイズを持つ。呼び出し側（APIやUI）は、ユーザーが指定した
    数値と実際の迷路サイズが1違うことがある前提で、常に返ってきた
    `Grid`の`width`/`height`を見て描画する必要がある。

    スタート・ゴール座標は規約として、生成された`Grid`の左上`(0, 0)`と
    右下`(grid.width - 1, grid.height - 1)`とする（`width`・`height`が
    共に奇数に調整済みのため、この2点は必ず部屋座標＝通路になる）。

    Args:
        width: 迷路の幅（3以上であること。偶数の場合は自動的に1減らす）。
        height: 迷路の高さ（3以上であること。偶数の場合は自動的に1減らす）。
        rng: 乱数生成器（`random.Random`互換）。省略時はデフォルトの
            `random`モジュールを使う。テストで生成結果を固定したい場合に
            `random.Random(seed)`を渡せる。

    Returns:
        生成済みの`Grid`（通路セルは`is_wall = False`）。

    Raises:
        ValueError: `width`または`height`が3未満の場合。
    """
    if width < 3 or height < 3:
        raise ValueError("width, height must be at least 3")

    if width % 2 == 0:
        width -= 1
    if height % 2 == 0:
        height -= 1

    rng = rng if rng is not None else random

    grid = Grid(width, height)

    start = (0, 0)
    grid.get_cell(*start).is_wall = False
    visited = {start}

    # 反復DFS（明示的なスタックを使う recursive backtracker）。
    # スタックの各要素は現在地の部屋座標。
    stack = [start]
    directions = [(2, 0), (-2, 0), (0, 2), (0, -2)]

    while stack:
        x, y = stack[-1]
        candidates = []
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if grid.in_bounds(nx, ny) and (nx, ny) not in visited:
                candidates.append((nx, ny, dx, dy))

        if not candidates:
            stack.pop()
            continue

        nx, ny, dx, dy = rng.choice(candidates)
        # 現在地と次の部屋の間（1マス先）の壁を取り払う。
        grid.get_cell(x + dx // 2, y + dy // 2).is_wall = False
        grid.get_cell(nx, ny).is_wall = False
        visited.add((nx, ny))
        stack.append((nx, ny))

    return grid
