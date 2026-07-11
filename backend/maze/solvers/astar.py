"""A*（A-star）による迷路の最短経路探索。

`Grid`上をスタートから4方向（上下左右のみ、斜め移動無し）に、`heapq`による
優先度付きキューを使って探索し、確定順で訪問したセルと最短経路をアニメーション
用のステップ列として記録する。優先度はスタートからの実コスト`g`とゴールまでの
マンハッタン距離ヒューリスティック`h`の和`f = g + h`。マンハッタン距離は
4方向移動・コスト1のグリッドにおいて許容的（admissible、実際のコストを
過大評価しない）かつ単調（consistent）であるため、Dijkstra法と同様「セルを
キューから取り出した時点」でそのセルの最短距離が確定していることが保証され、
最短経路が保証される。
"""

import heapq
import itertools

from steps import StepRecorder


def _heuristic(a, b):
    """`a`から`b`までのマンハッタン距離を返す（4方向移動の許容的ヒューリスティック）。"""
    (x1, y1), (x2, y2) = a, b
    return abs(x1 - x2) + abs(y1 - y2)


def solve_astar(grid, start, goal):
    """A*で`start`から`goal`への最短経路を探索する。

    優先度付きキュー（`heapq`、優先度は`f = g + h`）からセルを取り出し、
    そのセルの最短距離が確定した時点で`StepRecorder.record_visit`を呼ぶ
    （＝「確定順」で記録する。Dijkstra法と同じ規約）。同じセルが古い距離の
    まま複数回キューに積まれていても、既に確定済みのセルを取り出した場合は
    無視するだけで、記録は発生しない。壁（`is_wall=True`）のセルには進入
    しない。

    Args:
        grid: 探索対象の`Grid`。
        start: スタート座標`(x, y)`。
        goal: ゴール座標`(x, y)`。

    Returns:
        `StepRecorder`が記録したステップの`list[dict]`。訪問したセルの
        確定順に`visit`ステップが並び、ゴールに到達できた場合は末尾に
        `start`から`goal`までの最短経路（`[x, y]`ペアのリスト、両端含む）
        を表す`path`ステップが1件だけ追加される。ゴールに到達できない
        場合、`path`ステップは追加されず`visit`ステップのみが返る。
    """
    recorder = StepRecorder()

    g_score = {start: 0}
    came_from = {}
    settled = set()

    # heapqはタプルを要素ごとに比較するため、f値が同着の場合に座標タプル
    # 同士の比較へフォールバックしないよう、挿入順の連番をタイブレークに使う。
    counter = itertools.count()
    queue = [(_heuristic(start, goal), next(counter), start)]

    while queue:
        f, _, (x, y) = heapq.heappop(queue)

        if (x, y) in settled:
            continue

        settled.add((x, y))
        recorder.record_visit(x, y)

        if (x, y) == goal:
            break

        g = g_score[(x, y)]

        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not grid.in_bounds(nx, ny):
                continue
            if (nx, ny) in settled:
                continue
            if grid.get_cell(nx, ny).is_wall:
                continue

            ng = g + 1
            if ng < g_score.get((nx, ny), float("inf")):
                g_score[(nx, ny)] = ng
                came_from[(nx, ny)] = (x, y)
                nf = ng + _heuristic((nx, ny), goal)
                heapq.heappush(queue, (nf, next(counter), (nx, ny)))

    if goal in settled:
        path = [list(goal)]
        current = goal
        while current != start:
            current = came_from[current]
            path.append(list(current))
        path.reverse()
        recorder.record_path(path)

    return recorder.to_list()
