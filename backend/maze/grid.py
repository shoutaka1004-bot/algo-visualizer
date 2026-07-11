"""迷路のグリッド表現と、それを構成するセルのデータ構造。

このモジュールは純粋なデータ構造のみを提供する。迷路の生成（穴掘り法）や
探索アルゴリズム（BFS/Dijkstra/A*）は別モジュールが、この`Grid`/`Cell`を
土台として実装する。
"""


class Cell:
    """迷路グリッド上の1マス。

    Attributes:
        x: グリッド上のX座標（0始まり）。
        y: グリッド上のY座標（0始まり）。
        is_wall: 壁かどうか。穴掘り法は「全面壁の状態から通路を掘る」方式のため、
            デフォルトは`True`（壁）とする。
    """

    def __init__(self, x, y, is_wall=True):
        self.x = x
        self.y = y
        self.is_wall = is_wall

    def __repr__(self):
        return f"Cell(x={self.x}, y={self.y}, is_wall={self.is_wall})"


class Grid:
    """幅・高さを指定して初期化する迷路のグリッド。

    全セルは初期状態で`is_wall=True`（壁）として生成される。
    """

    def __init__(self, width, height):
        if width <= 0 or height <= 0:
            raise ValueError("width, height must be positive integers")
        self.width = width
        self.height = height
        self._cells = [
            [Cell(x, y) for x in range(width)] for y in range(height)
        ]

    def in_bounds(self, x, y):
        """座標(x, y)がグリッドの範囲内かどうかを返す。"""
        return 0 <= x < self.width and 0 <= y < self.height

    def get_cell(self, x, y):
        """座標(x, y)のセルを取得する。範囲外の場合は`IndexError`を送出する。"""
        if not self.in_bounds(x, y):
            raise IndexError(f"out of bounds: ({x}, {y})")
        return self._cells[y][x]

    def __iter__(self):
        """全セルを行優先（y昇順→x昇順）で走査するイテレータを返す。"""
        for row in self._cells:
            yield from row
