"""Dijkstra法による迷路の最短経路探索。

`Grid`上をスタートから4方向（上下左右のみ、斜め移動無し）に、`heapq`による
優先度付きキューを使って探索し、確定順で訪問したセルと最短経路をアニメーション
用のステップ列として記録する。今回の迷路は全ての移動コストが1（重み無し）の
ため最短経路長はBFSと必ず一致するが、優先度付きキューを用いた実装であること
自体が学習教材としての目的である。
"""

import heapq
import itertools

from steps import StepRecorder


def solve_dijkstra(grid, start, goal):
    """Dijkstra法で`start`から`goal`への最短経路を探索する。

    優先度付きキュー（`heapq`）からセルを取り出し、そのセルの最短距離が
    確定した時点で`StepRecorder.record_visit`を呼ぶ（＝「確定順」で記録
    する）。同じセルが古い距離のまま複数回キューに積まれていても、既に
    確定済みのセルを取り出した場合は無視するだけで、記録は発生しない。
    壁（`is_wall=True`）のセルには進入しない。

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

    dist = {start: 0}
    came_from = {}
    settled = set()

    # heapqはタプルを要素ごとに比較するため、距離が同着の場合に座標タプル
    # 同士の比較へフォールバックしないよう、挿入順の連番をタイブレークに使う。
    counter = itertools.count()
    queue = [(0, next(counter), start)]

    while queue:
        d, _, (x, y) = heapq.heappop(queue)

        if (x, y) in settled:
            continue

        settled.add((x, y))
        recorder.record_visit(x, y)

        if (x, y) == goal:
            break

        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not grid.in_bounds(nx, ny):
                continue
            if (nx, ny) in settled:
                continue
            if grid.get_cell(nx, ny).is_wall:
                continue

            nd = d + 1
            if nd < dist.get((nx, ny), float("inf")):
                dist[(nx, ny)] = nd
                came_from[(nx, ny)] = (x, y)
                heapq.heappush(queue, (nd, next(counter), (nx, ny)))

    if goal in settled:
        path = [list(goal)]
        current = goal
        while current != start:
            current = came_from[current]
            path.append(list(current))
        path.reverse()
        recorder.record_path(path)

    return recorder.to_list()
