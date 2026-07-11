"""クイックソートによる整数（または比較可能な値）のソート。

ピボットとの比較・実際の交換をアニメーション用のステップ列として記録する。
"""

from steps import StepRecorder


def sort_quick(values):
    """`values`をクイックソートでソートし、アニメーション用のステップ列を返す。

    `values`自体は変更しない（内部でコピーを作成してソートする）。
    各パーティションでは末尾要素をピボットとするLomuto分割方式を用いる。
    ピボットと要素を比較するたびに`StepRecorder.record_compare`を
    `[ピボットの現在のインデックス, 比較対象のインデックス]`の形で呼び、
    実際に配列内の要素を交換した場合のみ`StepRecorder.record_swap`を呼ぶ
    （比較しただけで交換しなかった場合、および交換対象が同一インデックス
    だった場合は呼ばない）。

    末尾要素をピボットに選ぶ単純な方式のため、既にソート済み・逆順に
    ソート済みの配列に対しては再帰が偏る最悪ケースになるが、その場合でも
    最終的な結果は正しくソートされる。

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
    _quicksort(result, 0, len(result) - 1, recorder)
    return recorder.to_list()


def _quicksort(arr, low, high, recorder):
    if low < high:
        pivot_final_index = _partition(arr, low, high, recorder)
        _quicksort(arr, low, pivot_final_index - 1, recorder)
        _quicksort(arr, pivot_final_index + 1, high, recorder)


def _partition(arr, low, high, recorder):
    pivot_index = high
    pivot = arr[pivot_index]
    i = low - 1

    for j in range(low, high):
        recorder.record_compare([pivot_index, j])
        if arr[j] < pivot:
            i += 1
            if i != j:
                arr[i], arr[j] = arr[j], arr[i]
                recorder.record_swap([i, j])

    if i + 1 != high:
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        recorder.record_swap([i + 1, high])

    return i + 1
