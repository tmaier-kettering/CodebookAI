"""
Tests for core/task.py -- the shared engine that replaced the six hardcoded
single/multi/keyword x batch/live pipelines.

Covers:
- TaskList rendering in all four formats
- build_output_model / build_strict_schema for every output field type
- render_prompt substitution of columns and lists
- validate_task catching unknown placeholders and dangling list refs
- Task.to_dict / from_dict round-trip (task file save/load)
"""

import pytest

from core.task import (
    DEFAULT_MODEL,
    OutputField,
    Task,
    TaskList,
    TaskValidationError,
    build_output_model,
    build_request_params,
    build_strict_schema,
    forbid_additional_props,
    is_reasoning_model,
    render_prompt,
    validate_task,
)


# ---------------------------------------------------------------------------
# forbid_additional_props (moved here from batch_processing/batch_creation.py)
# ---------------------------------------------------------------------------

class TestForbidAdditionalProps:
    def test_sets_flag_on_object(self):
        schema = {"type": "object", "properties": {"x": {"type": "string"}}}
        result = forbid_additional_props(schema)
        assert result["additionalProperties"] is False

    def test_recursive_nested_object(self):
        schema = {
            "type": "object",
            "properties": {
                "inner": {
                    "type": "object",
                    "properties": {"y": {"type": "integer"}},
                }
            },
        }
        result = forbid_additional_props(schema)
        assert result["additionalProperties"] is False
        assert result["properties"]["inner"]["additionalProperties"] is False

    def test_array_items_object(self):
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"z": {"type": "string"}},
            },
        }
        result = forbid_additional_props(schema)
        assert result["items"]["additionalProperties"] is False

    def test_non_object_schema_unchanged(self):
        schema = {"type": "string"}
        result = forbid_additional_props(schema)
        assert "additionalProperties" not in result

    def test_creates_empty_properties_on_object(self):
        schema = {"type": "object"}
        result = forbid_additional_props(schema)
        assert result["additionalProperties"] is False
        assert "properties" in result

    def test_does_not_modify_string_inside_array(self):
        schema = {"type": "array", "items": {"type": "string"}}
        result = forbid_additional_props(schema)
        assert "additionalProperties" not in result["items"]

    def test_handles_non_dict_gracefully(self):
        assert forbid_additional_props("string") == "string"
        assert forbid_additional_props(42) == 42


# ---------------------------------------------------------------------------
# TaskList rendering
# ---------------------------------------------------------------------------

class TestTaskListRender:
    def test_comma(self):
        assert TaskList(["a", "b", "c"], "comma").render() == "a, b, c"

    def test_hyphen(self):
        assert TaskList(["a", "b"], "hyphen").render() == "- a\n- b"

    def test_space(self):
        assert TaskList(["a", "b", "c"], "space").render() == "a b c"

    def test_newline(self):
        assert TaskList(["a", "b"], "newline").render() == "a\nb"

    def test_default_format_is_comma(self):
        assert TaskList(["a", "b"]).render() == "a, b"


# ---------------------------------------------------------------------------
# render_prompt
# ---------------------------------------------------------------------------

class TestRenderPrompt:
    def test_substitutes_column(self):
        task = Task(prompt="Quote: {quote}")
        assert render_prompt(task, {"quote": "hello"}) == "Quote: hello"

    def test_substitutes_list_constant_across_rows(self):
        task = Task(
            prompt="Allowed: {labels}\nQuote: {quote}",
            lists={"labels": TaskList(["pos", "neg"], "comma")},
        )
        out1 = render_prompt(task, {"quote": "a"})
        out2 = render_prompt(task, {"quote": "b"})
        assert "Allowed: pos, neg" in out1
        assert "Allowed: pos, neg" in out2
        assert "Quote: a" in out1
        assert "Quote: b" in out2

    def test_multiple_per_row_columns(self):
        task = Task(prompt="Q: {survey_q}\nText: {quote}")
        rendered = render_prompt(task, {"survey_q": "How was it?", "quote": "Great"})
        assert rendered == "Q: How was it?\nText: Great"

    def test_literal_text_outside_braces_is_constant(self):
        task = Task(prompt="Classify strictly. Text: {quote}")
        assert render_prompt(task, {"quote": "x"}).startswith("Classify strictly. Text:")

    def test_renders_system_text_explicitly(self):
        task = Task(prompt="{quote}", system="You are grading {quote}.")
        rendered = render_prompt(task, {"quote": "hi"}, text=task.system)
        assert rendered == "You are grading hi."

    def test_unresolved_placeholder_raises(self):
        task = Task(prompt="{nonexistent}")
        with pytest.raises(TaskValidationError):
            render_prompt(task, {"quote": "x"})

    def test_list_format_applied_in_prompt(self):
        task = Task(
            prompt="Labels:\n{labels}",
            lists={"labels": TaskList(["pos", "neg"], "hyphen")},
        )
        assert render_prompt(task, {}) == "Labels:\n- pos\n- neg"


# ---------------------------------------------------------------------------
# validate_task
# ---------------------------------------------------------------------------

class TestValidateTask:
    def _valid_task(self) -> Task:
        return Task(
            prompt="Allowed: {labels}\nQuote: {quote}",
            lists={"labels": TaskList(["pos", "neg"])},
            output_fields=[OutputField(name="label", type="choice", list_ref="labels")],
            carry_columns=["quote_id"],
        )

    def test_valid_task_passes(self):
        validate_task(self._valid_task(), columns=["quote", "quote_id"])

    def test_unknown_placeholder_column_raises(self):
        task = Task(
            prompt="{does_not_exist}",
            output_fields=[OutputField(name="kw", type="text_list")],
        )
        with pytest.raises(TaskValidationError, match="does_not_exist"):
            validate_task(task, columns=["quote"])

    def test_no_output_fields_raises(self):
        task = Task(prompt="{quote}")
        with pytest.raises(TaskValidationError, match="output field"):
            validate_task(task, columns=["quote"])

    def test_duplicate_output_field_names_raises(self):
        task = Task(
            prompt="{quote}",
            output_fields=[
                OutputField(name="label", type="free_text"),
                OutputField(name="label", type="number"),
            ],
        )
        with pytest.raises(TaskValidationError, match="unique"):
            validate_task(task, columns=["quote"])

    def test_choice_field_missing_list_ref_raises(self):
        task = Task(
            prompt="{quote}",
            output_fields=[OutputField(name="label", type="choice", list_ref=None)],
        )
        with pytest.raises(TaskValidationError, match="reference a list"):
            validate_task(task, columns=["quote"])

    def test_choice_field_dangling_list_ref_raises(self):
        task = Task(
            prompt="{quote}",
            output_fields=[OutputField(name="label", type="choice", list_ref="ghost")],
        )
        with pytest.raises(TaskValidationError, match="ghost"):
            validate_task(task, columns=["quote"])

    def test_carried_column_not_in_input_raises(self):
        task = Task(
            prompt="{quote}",
            output_fields=[OutputField(name="kw", type="text_list")],
            carry_columns=["missing_id"],
        )
        with pytest.raises(TaskValidationError, match="missing_id"):
            validate_task(task, columns=["quote"])

    def test_carry_only_column_not_in_prompt_is_fine(self):
        # quote_id is carried to output but never referenced in the prompt --
        # this must be allowed (the whole point of separating the two roles).
        task = Task(
            prompt="Quote: {quote}",
            output_fields=[OutputField(name="kw", type="text_list")],
            carry_columns=["quote_id"],
        )
        validate_task(task, columns=["quote", "quote_id"])

    def test_reports_multiple_errors_at_once(self):
        task = Task(prompt="{ghost}", output_fields=[])
        with pytest.raises(TaskValidationError) as exc_info:
            validate_task(task, columns=["quote"])
        msg = str(exc_info.value)
        assert "ghost" in msg
        assert "output field" in msg


# ---------------------------------------------------------------------------
# build_output_model / build_strict_schema -- one per field type
# ---------------------------------------------------------------------------

class TestBuildOutputModel:
    def test_choice_field_is_enum_constrained(self):
        task = Task(
            prompt="{quote}",
            lists={"labels": TaskList(["pos", "neg", "neutral"])},
            output_fields=[OutputField(name="label", type="choice", list_ref="labels")],
        )
        model = build_output_model(task)
        inst = model(label="pos")
        assert inst.label == "pos"
        with pytest.raises(Exception):
            model(label="not_a_label")

    def test_multi_choice_field_is_list_of_enum(self):
        task = Task(
            prompt="{quote}",
            lists={"labels": TaskList(["a", "b", "c"])},
            output_fields=[OutputField(name="labels_out", type="multi_choice", list_ref="labels")],
        )
        model = build_output_model(task)
        inst = model(labels_out=["a", "b"])
        assert inst.labels_out == ["a", "b"]
        with pytest.raises(Exception):
            model(labels_out=[])  # min_length=1
        with pytest.raises(Exception):
            model(labels_out=["not_valid"])

    def test_text_list_field(self):
        task = Task(prompt="{quote}", output_fields=[OutputField(name="keywords", type="text_list")])
        model = build_output_model(task)
        inst = model(keywords=["a", "b"])
        assert inst.keywords == ["a", "b"]
        with pytest.raises(Exception):
            model(keywords=[])

    def test_free_text_field(self):
        task = Task(prompt="{quote}", output_fields=[OutputField(name="summary", type="free_text")])
        model = build_output_model(task)
        assert model(summary="a reason").summary == "a reason"

    def test_number_field(self):
        task = Task(prompt="{quote}", output_fields=[OutputField(name="score", type="number")])
        model = build_output_model(task)
        assert model(score=4.5).score == 4.5

    def test_yes_no_field(self):
        task = Task(prompt="{quote}", output_fields=[OutputField(name="relevant", type="yes_no")])
        model = build_output_model(task)
        assert model(relevant=True).relevant is True

    def test_multiple_output_fields_combined(self):
        task = Task(
            prompt="{quote}",
            lists={"labels": TaskList(["pos", "neg"])},
            output_fields=[
                OutputField(name="label", type="choice", list_ref="labels"),
                OutputField(name="keywords", type="text_list"),
                OutputField(name="reason", type="free_text"),
            ],
        )
        model = build_output_model(task)
        inst = model(label="pos", keywords=["k1"], reason="because")
        assert (inst.label, inst.keywords, inst.reason) == ("pos", ["k1"], "because")

    def test_no_output_fields_raises(self):
        task = Task(prompt="{quote}")
        with pytest.raises(TaskValidationError):
            build_output_model(task)

    def test_extra_fields_forbidden(self):
        task = Task(prompt="{quote}", output_fields=[OutputField(name="summary", type="free_text")])
        model = build_output_model(task)
        with pytest.raises(Exception):
            model(summary="x", unexpected="y")


class TestBuildStrictSchema:
    def test_schema_forbids_additional_props(self):
        task = Task(prompt="{quote}", output_fields=[OutputField(name="summary", type="free_text")])
        schema = build_strict_schema(task)
        assert schema["additionalProperties"] is False

    def test_schema_has_field_names(self):
        task = Task(
            prompt="{quote}",
            lists={"labels": TaskList(["pos", "neg"])},
            output_fields=[
                OutputField(name="label", type="choice", list_ref="labels"),
                OutputField(name="score", type="number"),
            ],
        )
        schema = build_strict_schema(task)
        assert set(schema["properties"]) == {"label", "score"}


# ---------------------------------------------------------------------------
# Task.to_dict / from_dict round-trip (task file save/load)
# ---------------------------------------------------------------------------

class TestTaskSerialization:
    def test_round_trip(self):
        task = Task(
            prompt="Allowed: {labels}\nQuote: {quote}",
            system="Be terse.",
            lists={"labels": TaskList(["pos", "neg"], "hyphen")},
            output_fields=[
                OutputField(name="label", type="choice", list_ref="labels"),
                OutputField(name="keywords", type="text_list"),
            ],
            carry_columns=["quote_id"],
            model="o3",
            temperature=0.7,
            reasoning_effort="high",
            max_output_tokens=500,
        )
        restored = Task.from_dict(task.to_dict())
        assert restored.prompt == task.prompt
        assert restored.system == task.system
        assert restored.lists["labels"].values == ["pos", "neg"]
        assert restored.lists["labels"].format == "hyphen"
        assert [f.name for f in restored.output_fields] == ["label", "keywords"]
        assert restored.carry_columns == ["quote_id"]
        assert restored.model == "o3"
        assert restored.temperature == 0.7
        assert restored.reasoning_effort == "high"
        assert restored.max_output_tokens == 500

    def test_old_task_json_without_model_defaults(self):
        """Task files saved before model/params existed must still load."""
        restored = Task.from_dict({
            "prompt": "{quote}",
            "output_fields": [{"name": "label", "type": "free_text"}],
        })
        assert restored.model == DEFAULT_MODEL
        assert restored.temperature is None
        assert restored.reasoning_effort is None
        assert restored.max_output_tokens is None

    def test_round_trip_via_json(self):
        import json

        task = Task(
            prompt="{quote}",
            lists={"labels": TaskList(["a", "b"])},
            output_fields=[OutputField(name="label", type="choice", list_ref="labels")],
        )
        blob = json.dumps(task.to_dict())
        restored = Task.from_dict(json.loads(blob))
        assert restored.lists["labels"].values == ["a", "b"]

    def test_minimal_task_defaults(self):
        task = Task.from_dict({"prompt": "{quote}"})
        assert task.system is None
        assert task.lists == {}
        assert task.output_fields == []
        assert task.carry_columns == []
        assert task.model == DEFAULT_MODEL


# ---------------------------------------------------------------------------
# is_reasoning_model / build_request_params
# ---------------------------------------------------------------------------

class TestIsReasoningModel:
    @pytest.mark.parametrize("model", ["o1", "o1-mini", "o3", "o3-mini", "o4-mini", "gpt-5", "gpt-5-mini"])
    def test_reasoning_models(self, model):
        assert is_reasoning_model(model) is True

    @pytest.mark.parametrize("model", ["gpt-4o", "gpt-4o-mini", "gpt-4.1"])
    def test_standard_models(self, model):
        assert is_reasoning_model(model) is False


class TestBuildRequestParams:
    def _task(self, **kwargs) -> Task:
        return Task(prompt="{quote}", output_fields=[OutputField(name="x", type="free_text")], **kwargs)

    def test_standard_model_sends_temperature_not_reasoning(self):
        params = build_request_params(self._task(model="gpt-4o-mini", temperature=0.3, reasoning_effort="high"))
        assert params["model"] == "gpt-4o-mini"
        assert params["temperature"] == 0.3
        assert "reasoning" not in params

    def test_reasoning_model_sends_reasoning_not_temperature(self):
        params = build_request_params(self._task(model="o3", temperature=0.3, reasoning_effort="high"))
        assert params["model"] == "o3"
        assert params["reasoning"] == {"effort": "high"}
        assert "temperature" not in params

    def test_reasoning_model_without_effort_omits_reasoning_key(self):
        params = build_request_params(self._task(model="o3"))
        assert "reasoning" not in params

    def test_max_output_tokens_passes_through_for_both(self):
        std = build_request_params(self._task(model="gpt-4o-mini", max_output_tokens=200))
        reasoning = build_request_params(self._task(model="o3", max_output_tokens=200))
        assert std["max_output_tokens"] == 200
        assert reasoning["max_output_tokens"] == 200

    def test_unset_optional_params_omitted(self):
        params = build_request_params(self._task(model="gpt-4o-mini"))
        assert params == {"model": "gpt-4o-mini"}
