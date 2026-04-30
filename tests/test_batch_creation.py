"""
Tests for batch_processing/batch_creation.py

Covers:
- forbid_additional_props schema transformation
- generate_single_label_batch: JSONL output, prompt content, custom_id format, schema
- generate_multi_label_batch: JSONL output and array schema
- generate_keyword_extraction_batch: JSONL output
- Edge cases: empty input, non-ASCII text, punctuation-heavy text
"""

import io
import json

import pytest

from batch_processing.batch_creation import (
    forbid_additional_props,
    generate_single_label_batch,
    generate_multi_label_batch,
    generate_keyword_extraction_batch,
)


# ---------------------------------------------------------------------------
# forbid_additional_props
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
        # Passing a non-dict should be returned unchanged
        assert forbid_additional_props("string") == "string"
        assert forbid_additional_props(42) == 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_jsonl(buf: io.BytesIO) -> list[dict]:
    """Read all lines from a BytesIO and parse them as JSON."""
    buf.seek(0)
    return [json.loads(line) for line in buf.read().decode("utf-8").splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# generate_single_label_batch
# ---------------------------------------------------------------------------

class TestGenerateSingleLabelBatch:
    def test_returns_bytesio(self, sample_labels, sample_quotes):
        result = generate_single_label_batch(sample_labels, sample_quotes)
        assert isinstance(result, io.BytesIO)

    def test_has_jsonl_name(self, sample_labels, sample_quotes):
        result = generate_single_label_batch(sample_labels, sample_quotes)
        assert result.name == "batchinput.jsonl"

    def test_line_count_matches_quotes(self, sample_labels, sample_quotes):
        result = generate_single_label_batch(sample_labels, sample_quotes)
        lines = _parse_jsonl(result)
        assert len(lines) == len(sample_quotes)

    def test_custom_id_format(self, sample_labels, sample_quotes):
        result = generate_single_label_batch(sample_labels, sample_quotes)
        lines = _parse_jsonl(result)
        for i, line in enumerate(lines, start=1):
            assert line["custom_id"] == f"quote-{i:05d}", f"Wrong custom_id at index {i}"

    def test_prompt_contains_all_labels(self, sample_labels, sample_quotes):
        result = generate_single_label_batch(sample_labels, sample_quotes)
        lines = _parse_jsonl(result)
        for line in lines:
            content = line["body"]["input"][0]["content"]
            for label in sample_labels:
                assert label in content, f"Label '{label}' missing from prompt"

    def test_prompt_contains_quote_text(self, sample_labels, sample_quotes):
        result = generate_single_label_batch(sample_labels, sample_quotes)
        lines = _parse_jsonl(result)
        for line, quote in zip(lines, sample_quotes):
            assert quote in line["body"]["input"][0]["content"]

    def test_schema_strict_flag(self, sample_labels, sample_quotes):
        result = generate_single_label_batch(sample_labels, sample_quotes)
        lines = _parse_jsonl(result)
        for line in lines:
            fmt = line["body"]["text"]["format"]
            assert fmt["strict"] is True

    def test_schema_additional_props_false(self, sample_labels, sample_quotes):
        result = generate_single_label_batch(sample_labels, sample_quotes)
        lines = _parse_jsonl(result)
        for line in lines:
            schema = line["body"]["text"]["format"]["schema"]
            assert schema.get("additionalProperties") is False

    def test_metadata_includes_quote(self, sample_labels, sample_quotes):
        result = generate_single_label_batch(sample_labels, sample_quotes)
        lines = _parse_jsonl(result)
        for line, quote in zip(lines, sample_quotes):
            assert line["body"]["metadata"]["quote"] == quote

    def test_empty_quotes_returns_empty_jsonl(self, sample_labels):
        result = generate_single_label_batch(sample_labels, [])
        lines = _parse_jsonl(result)
        assert lines == []

    def test_nonascii_text_round_trips(self, sample_labels):
        quotes = ["Ünïcödé tëxt wïth spëcïäl châräctërs!", "日本語テキスト", "Héllo wörld"]
        result = generate_single_label_batch(sample_labels, quotes)
        lines = _parse_jsonl(result)
        assert len(lines) == 3
        assert "日本語テキスト" in lines[1]["body"]["input"][0]["content"]

    def test_punctuation_heavy_text(self, sample_labels):
        quotes = ['He said, "It\'s great!" — really? (Yes!) #amazing @user $100']
        result = generate_single_label_batch(sample_labels, quotes)
        lines = _parse_jsonl(result)
        assert len(lines) == 1

    def test_long_excerpt(self, sample_labels):
        long_quote = "This is a very long excerpt. " * 100
        result = generate_single_label_batch(sample_labels, [long_quote])
        lines = _parse_jsonl(result)
        assert len(lines) == 1

    def test_short_single_word_excerpt(self, sample_labels):
        result = generate_single_label_batch(sample_labels, ["great"])
        lines = _parse_jsonl(result)
        assert len(lines) == 1

    def test_url_endpoint_is_responses(self, sample_labels, sample_quotes):
        result = generate_single_label_batch(sample_labels, sample_quotes)
        lines = _parse_jsonl(result)
        for line in lines:
            assert line["url"] == "/v1/responses"
            assert line["method"] == "POST"


# ---------------------------------------------------------------------------
# generate_multi_label_batch
# ---------------------------------------------------------------------------

class TestGenerateMultiLabelBatch:
    def test_line_count_matches_quotes(self, sample_labels, sample_quotes):
        result = generate_multi_label_batch(sample_labels, sample_quotes)
        lines = _parse_jsonl(result)
        assert len(lines) == len(sample_quotes)

    def test_schema_label_field_is_array(self, sample_labels, sample_quotes):
        result = generate_multi_label_batch(sample_labels, sample_quotes)
        lines = _parse_jsonl(result)
        for line in lines:
            schema = line["body"]["text"]["format"]["schema"]
            label_prop = schema["properties"]["label"]
            assert label_prop["type"] == "array"

    def test_prompt_contains_all_labels(self, sample_labels, sample_quotes):
        result = generate_multi_label_batch(sample_labels, sample_quotes)
        lines = _parse_jsonl(result)
        for line in lines:
            content = line["body"]["input"][0]["content"]
            for label in sample_labels:
                assert label in content

    def test_empty_quotes(self, sample_labels):
        result = generate_multi_label_batch(sample_labels, [])
        assert _parse_jsonl(result) == []

    def test_nonascii_labels(self, sample_quotes):
        labels = ["positivo", "négative", "中立"]
        result = generate_multi_label_batch(labels, sample_quotes)
        lines = _parse_jsonl(result)
        assert len(lines) == len(sample_quotes)
        for line in lines:
            content = line["body"]["input"][0]["content"]
            assert "中立" in content


# ---------------------------------------------------------------------------
# generate_keyword_extraction_batch
# ---------------------------------------------------------------------------

class TestGenerateKeywordExtractionBatch:
    def test_line_count_matches_texts(self, sample_quotes):
        result = generate_keyword_extraction_batch(sample_quotes)
        lines = _parse_jsonl(result)
        assert len(lines) == len(sample_quotes)

    def test_custom_id_prefix_is_text(self, sample_quotes):
        result = generate_keyword_extraction_batch(sample_quotes)
        lines = _parse_jsonl(result)
        for i, line in enumerate(lines, start=1):
            assert line["custom_id"] == f"text-{i:05d}"

    def test_schema_has_keywords_array(self, sample_quotes):
        result = generate_keyword_extraction_batch(sample_quotes)
        lines = _parse_jsonl(result)
        for line in lines:
            schema = line["body"]["text"]["format"]["schema"]
            assert "keywords" in schema.get("properties", {})
            assert schema["properties"]["keywords"]["type"] == "array"

    def test_prompt_contains_text(self, sample_quotes):
        result = generate_keyword_extraction_batch(sample_quotes)
        lines = _parse_jsonl(result)
        for line, text in zip(lines, sample_quotes):
            user_msg = next(
                m for m in line["body"]["input"] if m["role"] == "user"
            )
            assert text in user_msg["content"]

    def test_empty_texts(self):
        result = generate_keyword_extraction_batch([])
        assert _parse_jsonl(result) == []
