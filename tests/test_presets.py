"""
Tests for core/presets.py -- the three built-in Task presets that replace the
old hardcoded single/multi/keyword tools as editable starting points.
"""

import pytest

from core.presets import PRESETS
from core.task import Task, TaskValidationError, build_output_model, validate_task


class TestPresets:
    @pytest.mark.parametrize("key", list(PRESETS))
    def test_preset_is_a_task(self, key):
        _, factory = PRESETS[key]
        assert isinstance(factory(), Task)

    @pytest.mark.parametrize("key", list(PRESETS))
    def test_preset_valid_once_lists_populated(self, key):
        """Presets ship with empty label lists (the user fills these in) --
        once populated with any values, the task must validate against a
        'text' column and build a real output model."""
        _, factory = PRESETS[key]
        task = factory()
        for lst in task.lists.values():
            lst.values = ["a", "b"]
        validate_task(task, columns=["text"])
        build_output_model(task)  # must not raise

    @pytest.mark.parametrize("key", list(PRESETS))
    def test_preset_prompt_references_text_column(self, key):
        _, factory = PRESETS[key]
        assert "{text}" in factory().prompt

    def test_single_label_preset_is_choice(self):
        task = PRESETS["single_label"][1]()
        assert task.output_fields[0].type == "choice"
        assert task.output_fields[0].list_ref == "labels"

    def test_multi_label_preset_is_multi_choice(self):
        task = PRESETS["multi_label"][1]()
        assert task.output_fields[0].type == "multi_choice"

    def test_keyword_preset_has_no_list_dependency(self):
        task = PRESETS["keyword_extraction"][1]()
        assert task.lists == {}
        assert task.output_fields[0].type == "text_list"

    def test_empty_labels_list_accepts_no_value(self):
        """An unpopulated preset label list builds a model (structurally
        valid) but with zero allowed enum values -- so it can never actually
        be satisfied, which is exactly the nudge to fill labels in first."""
        task = PRESETS["single_label"][1]()
        model = build_output_model(task)
        with pytest.raises(Exception):
            model(label="anything")
