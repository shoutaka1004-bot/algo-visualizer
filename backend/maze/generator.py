"""迷路生成アルゴリズム（穴掘り法／recursive backtracker）。

`Grid`/`Cell`はセル単体が壁かどうかしか表現できない（壁を独立した区画として
持たない）ため、素朴に隣接セルを1マスずつ掘ると全セルが連結してしまい壁が
一切残らず、迷路として成立しない。そのため、このモジュールでは以下の
「二重解像度」の考え方を採用する。

- 座標が奇数(x, y)（かつ`1 <= x <= width - 2`、`1 <= y <= height - 2`）の
  セルのみを「部屋」とする。外周（x=0、x=width-1、y=0、y=height-1）は
  部屋の対象外のため、DFSでは一切訪問されず、壁のまま残る。これにより
  生成される迷路は自然に外周が壁で囲まれた見た目になる。
- 部屋から2マス離れた隣の部屋へ進む際、その間（1マス先）の壁も同時に
  取り払うことで、部屋同士をつなぐ通路を作る。
- 全ての部屋を訪問し終えると、通路セル全体が単一の全域木（スパニング
  ツリー）になり、部屋同士は構造上必ず連結する。
- スタート`(0, 0)`・ゴール`(width - 1, height - 1)`は外周の角にあり
  部屋の対象外（＝壁のまま）なので、生成後に個別に通路化し、それぞれ
  最も近い部屋へ繋がる中間セルも通路にすることで「入口」「出口」の
  穴を開ける。

この方式は部屋が奇数座標にしか存在できないため、内部的には
width・heightが共に奇数であることを前提に生成する。
"""

import random


from .grid import Grid


def generate_maze(width, height, rng=None):
    """穴掘り法（recursive backtracker）で迷路を生成する。

    `width`・`height`が偶数の場合、部屋（奇数座標のセル）の格子に収まる
    よう内部で1減らし、直近の奇数に自動調整してから生成する
    （例: width=10 → 実際には9で生成する）。返り値の`Grid`は、この
    調整後の実サイズを持つ。呼び出し側（APIやUI）は、ユーザーが指定した
    数値と実際の迷路サイズが1違うことがある前提で、常に返ってきた
    `Grid`の`width`/`height`を見て描画する必要がある。

    スタート・ゴール座標は規約として、生成された`Grid`の左上`(0, 0)`と
    右下`(grid.width - 1, grid.height - 1)`とする。この2点と、それぞれ
    最も近い部屋（`(1, 1)`・`(width - 2, height - 2)`）へ繋がる中間セル
    1つずつだけが外周上の「入口」「出口」として通路になり、それ以外の
    外周セルは壁のまま残る。

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

    # 部屋は奇数座標(1, 1)〜(width - 2, height - 2)の範囲にのみ存在する。
    start_room = (1, 1)
    grid.get_cell(*start_room).is_wall = False
    visited = {start_room}

    # 反復DFS（明示的なスタックを使う recursive backtracker）。
    # スタックの各要素は現在地の部屋座標。
    stack = [start_room]
    directions = [(2, 0), (-2, 0), (0, 2), (0, -2)]

    while stack:
        x, y = stack[-1]
        candidates = []
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            in_room_bounds = 1 <= nx <= width - 2 and 1 <= ny <= height - 2
            if in_room_bounds and (nx, ny) not in visited:
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

    # スタート(0, 0)を通路にし、最も近い部屋(1, 1)へ繋がる中間セル(1, 0)も
    # 通路にすることで、外周に「入口」の穴を1つだけ開ける。
    grid.get_cell(0, 0).is_wall = False
    grid.get_cell(1, 0).is_wall = False

    # ゴール(width - 1, height - 1)を通路にし、最も近い部屋
    # (width - 2, height - 2)へ繋がる中間セル(width - 2, height - 1)も
    # 通路にすることで、外周に「出口」の穴を1つだけ開ける。
    grid.get_cell(width - 1, height - 1).is_wall = False
    grid.get_cell(width - 2, height - 1).is_wall = False

    return grid
