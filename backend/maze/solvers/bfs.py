"""BFS（幅優先探索）による迷路の最短経路探索。

`Grid`上をスタートから4方向（上下左右のみ、斜め移動無し）に幅優先探索し、
訪問したセルの順序と最短経路をアニメーション用のステップ列として記録する。
"""

from collections import deque

from steps import StepRecorder


def solve_bfs(grid, start, goal):
    """BFSで`start`から`goal`への最短経路を探索する。

    `start`をキューに入れた時点、および隣接セルを新規にキューへ追加する
    たびに`StepRecorder.record_visit`を呼ぶ（＝「発見順」で記録する）。
    壁（`is_wall=True`）のセルには進入しない。

    Args:
        grid: 探索対象の`Grid`。
        start: スタート座標`(x, y)`。
        goal: ゴール座標`(x, y)`。

    Returns:
        `StepRecorder`が記録したステップの`list[dict]`。訪問したセルの
        発見順に`visit`ステップが並び、ゴールに到達できた場合は末尾に
        `start`から`goal`までの最短経路（`[x, y]`ペアのリスト、両端含む）
        を表す`path`ステップが1件だけ追加される。ゴールに到達できない
        場合、`path`ステップは追加されず`visit`ステップのみが返る。
    """
    recorder = StepRecorder()

    visited = {start}
    came_from = {}
    queue = deque([start])
    recorder.record_visit(*start)

    found = start == goal

    while queue and not found:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not grid.in_bounds(nx, ny):
                continue
            if (nx, ny) in visited:
                continue
            if grid.get_cell(nx, ny).is_wall:
                continue

            visited.add((nx, ny))
            came_from[(nx, ny)] = (x, y)
            recorder.record_visit(nx, ny)
            queue.append((nx, ny))

            if (nx, ny) == goal:
                found = True
                break

    if found:
        path = [list(goal)]
        current = goal
        while current != start:
            current = came_from[current]
            path.append(list(current))
        path.reverse()
        recorder.record_path(path)

    return recorder.to_list()
