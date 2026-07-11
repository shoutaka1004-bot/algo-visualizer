"""マージソートによる整数（または比較可能な値）のソート。

分割した部分列の比較と、一時バッファから配列への書き戻しを
アニメーション用のステップ列として記録する。
"""

from steps import StepRecorder


def sort_merge(values):
    """`values`をマージソートでソートし、アニメーション用のステップ列を返す。

    `values`自体は変更しない（内部でコピーを作成してソートする）。

    マージソートは「配列内の2要素を直接交換（swap）」という操作を
    本質的には行わない（分割→それぞれソート→マージ時に一時バッファから
    値を書き戻す、という流れのため）。そのため本実装では`swap`は一切
    使わず、代わりに`StepRecorder.record_overwrite`を用いて、マージ時に
    一時バッファから配列へ値を1件書き戻すたびにその操作を記録する。
    左右の部分列の先頭同士を比較するたびに`StepRecorder.record_compare`を
    `[左側要素の元配列での絶対インデックス, 右側要素の元配列での絶対インデックス]`
    の形で呼ぶ（片方の部分列を使い切った後の残り要素の書き戻しは、比較を
    伴わないため`record_compare`は呼ばない）。

    Args:
        values: ソート対象の比較可能な値のリスト。

    Returns:
        `StepRecorder`が記録したステップ（`compare`/`overwrite`のみ）の
        `list[dict]`。ソート済みの配列そのものはこの戻り値には含まれない。
        呼び出し側（フロントエンド）が元の`values`に対して記録された
        ステップを順に適用することで、最終的なソート済み配列を再現できる。
    """
    recorder = StepRecorder()
    result = list(values)
    _merge_sort(result, 0, len(result) - 1, recorder)
    return recorder.to_list()


def _merge_sort(arr, low, high, recorder):
    if low >= high:
        return
    mid = (low + high) // 2
    _merge_sort(arr, low, mid, recorder)
    _merge_sort(arr, mid + 1, high, recorder)
    _merge(arr, low, mid, high, recorder)


def _merge(arr, low, mid, high, recorder):
    left = arr[low:mid + 1]
    right = arr[mid + 1:high + 1]
    i = j = 0
    k = low

    while i < len(left) and j < len(right):
        recorder.record_compare([low + i, mid + 1 + j])
        if left[i] <= right[j]:
            arr[k] = left[i]
            recorder.record_overwrite(k, left[i])
            i += 1
        else:
            arr[k] = right[j]
            recorder.record_overwrite(k, right[j])
            j += 1
        k += 1

    while i < len(left):
        arr[k] = left[i]
        recorder.record_overwrite(k, left[i])
        i += 1
        k += 1

    while j < len(right):
        arr[k] = right[j]
        recorder.record_overwrite(k, right[j])
        j += 1
        k += 1
