import json

from steps import StepRecorder


def test_empty_recorder_returns_empty_list():
    recorder = StepRecorder()
    assert recorder.to_list() == []


def test_record_visit_appends_visit_step():
    recorder = StepRecorder()
    recorder.record_visit(1, 2)
    assert recorder.to_list() == [{"type": "visit", "x": 1, "y": 2}]


def test_record_path_appends_path_step():
    recorder = StepRecorder()
    recorder.record_path([[0, 0], [0, 1], [1, 1]])
    assert recorder.to_list() == [
        {"type": "path", "cells": [[0, 0], [0, 1], [1, 1]]}
    ]


def test_record_compare_appends_compare_step():
    recorder = StepRecorder()
    recorder.record_compare([0, 1])
    assert recorder.to_list() == [{"type": "compare", "indices": [0, 1]}]


def test_record_swap_appends_swap_step():
    recorder = StepRecorder()
    recorder.record_swap([2, 3])
    assert recorder.to_list() == [{"type": "swap", "indices": [2, 3]}]


def test_record_overwrite_appends_overwrite_step():
    recorder = StepRecorder()
    recorder.record_overwrite(4, 10)
    assert recorder.to_list() == [{"type": "overwrite", "index": 4, "value": 10}]


def test_steps_are_returned_in_recorded_order():
    recorder = StepRecorder()
    recorder.record_visit(0, 0)
    recorder.record_compare([0, 1])
    recorder.record_swap([0, 1])
    recorder.record_path([[0, 0]])

    types = [step["type"] for step in recorder.to_list()]
    assert types == ["visit", "compare", "swap", "path"]


def test_to_list_returns_a_copy_not_internal_reference():
    recorder = StepRecorder()
    recorder.record_visit(0, 0)
    steps = recorder.to_list()
    steps.append({"type": "visit", "x": 9, "y": 9})
    assert len(recorder.to_list()) == 1


def test_generic_add_supports_arbitrary_step_types():
    recorder = StepRecorder()
    recorder.add("custom", foo="bar")
    assert recorder.to_list() == [{"type": "custom", "foo": "bar"}]


def test_recorded_steps_are_json_serializable():
    recorder = StepRecorder()
    recorder.record_visit(1, 2)
    recorder.record_path([[0, 0], [1, 0]])
    recorder.record_compare([0, 1])
    recorder.record_swap([1, 2])

    json_text = json.dumps(recorder.to_list())
    round_tripped = json.loads(json_text)

    assert round_tripped == recorder.to_list()
