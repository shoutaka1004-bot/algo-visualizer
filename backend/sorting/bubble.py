"""バブルソートによる整数（または比較可能な値）のソート。

隣接要素の比較・交換をアニメーション用のステップ列として記録する。
"""

from steps import StepRecorder


def sort_bubble(values):
    """`values`をバブルソートでソートし、アニメーション用のステップ列を返す。

    `values`自体は変更しない（内部でコピーを作成してソートする）。
    隣接する2要素を比較するたびに`StepRecorder.record_compare`を呼び、
    実際に交換が発生した場合のみ`StepRecorder.record_swap`を呼ぶ
    （比較しただけで交換しなかった場合は呼ばない）。

    各パスで1回も交換が発生しなかった時点で残りは既にソート済みと判断し、
    それ以降のパスは行わない（標準的な早期終了の最適化）。

    Args:
        values: ソート対象の比較可能な値のリスト。

    Returns:
        `StepRecorder`が記録したステップの`list[dict]`。ソート済みの
        配列そのものはこの戻り値には含まれない。呼び出し側（フロント
        エンド）が元の`values`に対して記録された`compare`/`swap`ステップ
        を順に適用することで、最終的なソート済み配列を再現できる。
    """
    recorder = StepRecorder()
    result = list(values)
    n = len(result)

    for pass_end in range(n - 1, 0, -1):
        swapped = False
        for i in range(pass_end):
            j = i + 1
            recorder.record_compare([i, j])
            if result[i] > result[j]:
                result[i], result[j] = result[j], result[i]
                recorder.record_swap([i, j])
                swapped = True
        if not swapped:
            break

    return recorder.to_list()
