"""アルゴリズムの実行ステップを記録する共通フォーマット。

迷路探索（BFS/Dijkstra/A*）とソート（バブル/クイック/マージ）の両方が、
アニメーション用の状態遷移をこのモジュールを通して記録する。記録結果は
`dict`のリストであり、そのままJSONとしてフロントエンドに渡すことを想定する。

過度なクラス階層は設けず、`StepRecorder`という単一の記録役クラスが
辞書のリストを組み立てるだけのシンプルな設計とする。
"""


class StepRecorder:
    """ステップ（`dict`）のリストを組み立てる記録役。

    対応するステップ種別（`type`）:
        visit: 迷路探索でのセル訪問。
        path: 迷路探索での最終経路。
        compare: ソートでの比較。
        swap: ソートでの交換。
    """

    def __init__(self):
        self._steps = []

    def add(self, type, **fields):
        """任意の種別のステップを1件追記する。

        `record_*`系のヘルパーで対応できない新しい種別が今後必要になった
        場合のための汎用エントリポイント。
        """
        self._steps.append({"type": type, **fields})

    def record_visit(self, x, y):
        """迷路探索でセル(x, y)を訪問したことを記録する。"""
        self.add("visit", x=x, y=y)

    def record_path(self, cells):
        """迷路探索の最終経路（[x, y]ペアのリスト）を記録する。"""
        self.add("path", cells=cells)

    def record_compare(self, indices):
        """ソートで比較したインデックスのリストを記録する。"""
        self.add("compare", indices=indices)

    def record_swap(self, indices):
        """ソートで交換したインデックスのリストを記録する。"""
        self.add("swap", indices=indices)

    def to_list(self):
        """記録済みの全ステップを、記録した順の`list[dict]`として返す。"""
        return list(self._steps)
