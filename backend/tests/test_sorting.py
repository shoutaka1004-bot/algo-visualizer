import random

from sorting.bubble import sort_bubble
from sorting.merge import sort_merge
from sorting.quick import sort_quick


def _apply_steps(values, steps):
    """`compare`/`swap`/`overwrite`ステップを`values`のコピーに順に適用し、
    最終状態を返す。

    `swap`・`overwrite`ステップが実際に配列の状態を変える（`compare`は
    観測のみ）。フロントエンド側の再構築ロジックを模したヘルパー。
    マージソートは`swap`を使わず`overwrite`（インデックスへの値の書き戻し）
    で状態を変える。
    """
    result = list(values)
    for step in steps:
        if step["type"] == "swap":
            i, j = step["indices"]
            result[i], result[j] = result[j], result[i]
        elif step["type"] == "overwrite":
            result[step["index"]] = step["value"]
    return result


def test_sort_bubble_returns_only_compare_and_swap_steps():
    steps = sort_bubble([3, 1, 2])
    types = {step["type"] for step in steps}
    assert types <= {"compare", "swap"}
    assert any(step["type"] == "compare" for step in steps)
    assert any(step["type"] == "swap" for step in steps)


def test_sort_bubble_steps_reconstruct_sorted_array():
    values = [3, 1, 2]
    steps = sort_bubble(values)
    assert _apply_steps(values, steps) == sorted(values)


def test_sort_bubble_does_not_mutate_input():
    values = [5, 4, 3, 2, 1]
    original = list(values)
    sort_bubble(values)
    assert values == original


def test_sort_bubble_already_sorted_has_no_swaps():
    steps = sort_bubble([1, 2, 3, 4])
    assert all(step["type"] != "swap" for step in steps)


def test_sort_bubble_reverse_order():
    values = [5, 4, 3, 2, 1]
    steps = sort_bubble(values)
    assert _apply_steps(values, steps) == sorted(values)


def test_sort_bubble_handles_duplicates():
    values = [3, 1, 3, 2, 1]
    steps = sort_bubble(values)
    assert _apply_steps(values, steps) == sorted(values)


def test_sort_bubble_empty_list():
    steps = sort_bubble([])
    assert steps == []


def test_sort_bubble_single_element():
    steps = sort_bubble([42])
    assert all(step["type"] != "swap" for step in steps)
    assert _apply_steps([42], steps) == [42]


def test_sort_bubble_random_array_matches_builtin_sorted():
    rng = random.Random(12345)
    values = [rng.randint(-100, 100) for _ in range(30)]
    steps = sort_bubble(values)
    assert _apply_steps(values, steps) == sorted(values)


def test_sort_quick_returns_only_compare_and_swap_steps():
    steps = sort_quick([3, 1, 2])
    types = {step["type"] for step in steps}
    assert types <= {"compare", "swap"}
    assert any(step["type"] == "compare" for step in steps)
    assert any(step["type"] == "swap" for step in steps)


def test_sort_quick_steps_reconstruct_sorted_array():
    values = [3, 1, 2]
    steps = sort_quick(values)
    assert _apply_steps(values, steps) == sorted(values)


def test_sort_quick_does_not_mutate_input():
    values = [5, 4, 3, 2, 1]
    original = list(values)
    sort_quick(values)
    assert values == original


def test_sort_quick_reverse_order():
    values = [5, 4, 3, 2, 1]
    steps = sort_quick(values)
    assert _apply_steps(values, steps) == sorted(values)


def test_sort_quick_handles_duplicates():
    values = [3, 1, 3, 2, 1]
    steps = sort_quick(values)
    assert _apply_steps(values, steps) == sorted(values)


def test_sort_quick_empty_list():
    steps = sort_quick([])
    assert steps == []


def test_sort_quick_single_element():
    steps = sort_quick([42])
    assert all(step["type"] != "swap" for step in steps)
    assert _apply_steps([42], steps) == [42]


def test_sort_quick_random_array_matches_builtin_sorted():
    rng = random.Random(12345)
    values = [rng.randint(-100, 100) for _ in range(30)]
    steps = sort_quick(values)
    assert _apply_steps(values, steps) == sorted(values)


def test_sort_quick_already_sorted_worst_case_still_sorts_correctly():
    # 末尾要素をピボットに選ぶLomuto分割方式では、既にソート済みの配列は
    # 各パーティションが1要素ずつしか減らない最悪ケース（再帰が偏るケース）
    # になる。それでも最終結果が正しくソートされることを確認する。
    values = list(range(50))
    steps = sort_quick(values)
    assert _apply_steps(values, steps) == sorted(values)


def test_sort_merge_returns_only_compare_and_overwrite_steps():
    # マージソートは配列内の2要素を直接交換(swap)しないため、swapは一切
    # 出力されない。
    steps = sort_merge([3, 1, 2])
    types = {step["type"] for step in steps}
    assert types <= {"compare", "overwrite"}
    assert all(step["type"] != "swap" for step in steps)
    assert any(step["type"] == "compare" for step in steps)
    assert any(step["type"] == "overwrite" for step in steps)


def test_sort_merge_steps_reconstruct_sorted_array():
    values = [3, 1, 2]
    steps = sort_merge(values)
    assert _apply_steps(values, steps) == sorted(values)


def test_sort_merge_does_not_mutate_input():
    values = [5, 4, 3, 2, 1]
    original = list(values)
    sort_merge(values)
    assert values == original


def test_sort_merge_reverse_order():
    values = [5, 4, 3, 2, 1]
    steps = sort_merge(values)
    assert _apply_steps(values, steps) == sorted(values)


def test_sort_merge_handles_duplicates():
    values = [3, 1, 3, 2, 1]
    steps = sort_merge(values)
    assert _apply_steps(values, steps) == sorted(values)


def test_sort_merge_empty_list():
    steps = sort_merge([])
    assert steps == []


def test_sort_merge_single_element():
    steps = sort_merge([42])
    assert all(step["type"] != "overwrite" for step in steps)
    assert _apply_steps([42], steps) == [42]


def test_sort_merge_random_array_matches_builtin_sorted():
    rng = random.Random(12345)
    values = [rng.randint(-100, 100) for _ in range(30)]
    steps = sort_merge(values)
    assert _apply_steps(values, steps) == sorted(values)
