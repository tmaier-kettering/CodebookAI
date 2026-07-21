"""
Tests for batch_processing/batch_creation.py

The old single/multi/keyword generate_*_batch functions are gone -- one
generate_batch(task, rows) now covers every shape. Covers:
- JSONL structure: custom_id format, endpoint, model
- Prompt rendering (per-row columns + constant lists) reaches the request body
- System message only appears when the task defines one
- Strict schema (additionalProperties: false) is attached
- Edge cases: empty rows, non-ASCII, multiple output fields
"""

import io
import json

from batch_processing.batch_creation import generate_batch
from core.task import OutputField, Task, TaskList


def _parse_jsonl(buf: io.BytesIO) -> list[dict]:
    buf.seek(0)
    return [json.loads(line) for line in buf.read().decode("utf-8").splitlines() if line.strip()]


def _single_label_task(labels=("positive", "negative", "neutral")) -> Task:
    return Task(
        prompt="Label this quote with exactly one label from the allowed set.\nAllowed: {labels}\nQuote: {quote}",
        lists={"labels": TaskList(list(labels), "comma")},
        output_fields=[OutputField(name="label", type="choice", list_ref="labels")],
    )


class TestGenerateBatch:
    def test_returns_bytesio_named_jsonl(self):
        result = generate_batch(_single_label_task(), [{"quote": "hi"}])
        assert isinstance(result, io.BytesIO)
        assert result.name == "batchinput.jsonl"

    def test_line_count_matches_rows(self):
        rows = [{"quote": "a"}, {"quote": "b"}, {"quote": "c"}]
        lines = _parse_jsonl(generate_batch(_single_label_task(), rows))
        assert len(lines) == 3

    def test_custom_id_format(self):
        rows = [{"quote": f"q{i}"} for i in range(3)]
        lines = _parse_jsonl(generate_batch(_single_label_task(), rows))
        for i, line in enumerate(lines, start=1):
            assert line["custom_id"] == f"row-{i:05d}"

    def test_prompt_contains_rendered_labels_and_quote(self):
        rows = [{"quote": "great product"}]
        lines = _parse_jsonl(generate_batch(_single_label_task(), rows))
        content = lines[0]["body"]["input"][-1]["content"]
        assert "positive" in content and "negative" in content and "neutral" in content
        assert "great product" in content

    def test_no_system_message_when_task_has_none(self):
        lines = _parse_jsonl(generate_batch(_single_label_task(), [{"quote": "x"}]))
        assert len(lines[0]["body"]["input"]) == 1
        assert lines[0]["body"]["input"][0]["role"] == "user"

    def test_system_message_present_when_task_defines_one(self):
        task = Task(
            prompt="Extract keywords.\nText: {text}",
            system="You are an expert at structured data extraction.",
            output_fields=[OutputField(name="keywords", type="text_list")],
        )
        lines = _parse_jsonl(generate_batch(task, [{"text": "hello world"}]))
        roles = [m["role"] for m in lines[0]["body"]["input"]]
        assert roles == ["system", "user"]
        assert lines[0]["body"]["input"][0]["content"] == "You are an expert at structured data extraction."

    def test_schema_strict_and_forbids_additional_props(self):
        lines = _parse_jsonl(generate_batch(_single_label_task(), [{"quote": "x"}]))
        fmt = lines[0]["body"]["text"]["format"]
        assert fmt["strict"] is True
        assert fmt["schema"]["additionalProperties"] is False

    def test_no_metadata_key_in_request_body(self):
        """Row data is no longer round-tripped through OpenAI request metadata
        (512-char limit risk) -- carried columns are joined locally instead."""
        lines = _parse_jsonl(generate_batch(_single_label_task(), [{"quote": "x"}]))
        assert "metadata" not in lines[0]["body"]

    def test_empty_rows_returns_empty_jsonl(self):
        assert _parse_jsonl(generate_batch(_single_label_task(), [])) == []

    def test_nonascii_text_round_trips(self):
        rows = [{"quote": "日本語テキスト"}]
        lines = _parse_jsonl(generate_batch(_single_label_task(), rows))
        assert "日本語テキスト" in lines[0]["body"]["input"][0]["content"]

    def test_url_and_method(self):
        lines = _parse_jsonl(generate_batch(_single_label_task(), [{"quote": "x"}]))
        assert lines[0]["url"] == "/v1/responses"
        assert lines[0]["method"] == "POST"

    def test_multiple_output_fields_in_schema(self):
        task = Task(
            prompt="{quote}",
            lists={"labels": TaskList(["a", "b"])},
            output_fields=[
                OutputField(name="label", type="choice", list_ref="labels"),
                OutputField(name="reason", type="free_text"),
            ],
        )
        lines = _parse_jsonl(generate_batch(task, [{"quote": "x"}]))
        props = lines[0]["body"]["text"]["format"]["schema"]["properties"]
        assert set(props) == {"label", "reason"}

    def test_extra_columns_not_referenced_in_prompt_are_ignored(self):
        """A carry-only column (e.g. quote_id) exists in the row dict but
        isn't a {placeholder} -- it must not appear in the prompt text."""
        rows = [{"quote": "hello", "quote_id": "R001"}]
        lines = _parse_jsonl(generate_batch(_single_label_task(), rows))
        content = lines[0]["body"]["input"][0]["content"]
        assert "R001" not in content

    def test_multiple_per_row_placeholders(self):
        task = Task(
            prompt="Q: {survey_q}\nA: {quote}",
            output_fields=[OutputField(name="summary", type="free_text")],
        )
        rows = [{"survey_q": "How was it?", "quote": "Great"}]
        lines = _parse_jsonl(generate_batch(task, rows))
        content = lines[0]["body"]["input"][0]["content"]
        assert content == "Q: How was it?\nA: Great"
