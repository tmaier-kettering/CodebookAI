"""
Tests for batch_processing/batch_method.py

Covers:
- _safe_parse_model_text: valid JSON, fenced JSON, truncated JSON, non-JSON,
  completely unparsable, empty string, whitespace
- get_client: missing API key raises, valid key returns client
- get_batch_results: successful response, malformed rows, missing output file
- Authentication failures, rate limit errors, timeout/connection errors are
  all handled via the same Exception path that get_batch_results delegates to
  the caller (get_client raises, or the mock client raises).
"""

import json
from unittest.mock import MagicMock

import pytest

from batch_processing.batch_method import (
    _safe_parse_model_text,
    get_batch_results,
    get_client,
)


# ---------------------------------------------------------------------------
# _safe_parse_model_text
# ---------------------------------------------------------------------------

class TestSafeParseModelText:
    """Tests for the internal JSON-parsing/repair helper."""

    def test_valid_json_returns_dict_no_error(self):
        result, err = _safe_parse_model_text('{"label": "positive"}')
        assert result == {"label": "positive"}
        assert err is None

    def test_valid_json_multi_key(self):
        result, err = _safe_parse_model_text('{"label": "positive", "confidence": 0.9}')
        assert result["label"] == "positive"
        assert err is None

    def test_whitespace_around_json(self):
        result, err = _safe_parse_model_text('  \n{"label": "neutral"}\n  ')
        assert result == {"label": "neutral"}
        assert err is None

    def test_fenced_json_single_backtick_block(self):
        text = '```json\n{"label": "negative"}\n```'
        result, err = _safe_parse_model_text(text)
        assert result == {"label": "negative"}
        assert err is None

    def test_fenced_json_no_language_tag(self):
        text = '```\n{"label": "positive"}\n```'
        result, err = _safe_parse_model_text(text)
        assert result == {"label": "positive"}
        assert err is None

    def test_truncated_json_brace_label(self):
        """Truncated '{"label":"disapproval' should be repaired."""
        result, err = _safe_parse_model_text('{"label":"negative')
        assert result is not None
        assert result.get("label") == "negative"
        assert err is not None  # repair note present

    def test_non_json_label_colon_format(self):
        """'label: positive' should be recovered."""
        result, err = _safe_parse_model_text('label: positive')
        assert result is not None
        assert result.get("label") == "positive"
        assert err is not None

    def test_non_json_label_equals_format(self):
        result, err = _safe_parse_model_text('label = "negative"')
        assert result is not None
        assert result.get("label") == "negative"
        assert err is not None

    def test_completely_unparsable_returns_none(self):
        result, err = _safe_parse_model_text("COMPLETELY RANDOM UNSTRUCTURED OUTPUT XYZ")
        assert result is None
        assert err is not None

    def test_empty_string_returns_none(self):
        result, err = _safe_parse_model_text("")
        assert result is None
        assert err is not None

    def test_whitespace_only_returns_none(self):
        result, err = _safe_parse_model_text("   \n\t  ")
        assert result is None
        assert err is not None

    def test_json_array_returns_parsed(self):
        """A JSON array is valid JSON and should be parsed as-is."""
        result, err = _safe_parse_model_text('["positive", "negative"]')
        assert result == ["positive", "negative"]
        assert err is None

    def test_truncated_label_with_spaces(self):
        """Truncation mid-value with a space in the value."""
        result, err = _safe_parse_model_text('{"label":"strongly positive')
        assert result is not None
        assert "label" in result


# ---------------------------------------------------------------------------
# get_client
# ---------------------------------------------------------------------------

class TestGetClient:
    def test_raises_when_no_api_key(self, mocker):
        mocker.patch(
            "batch_processing.batch_method.secrets_store.load_api_key",
            return_value=None,
        )
        with pytest.raises(Exception, match="API key not configured"):
            get_client()

    def test_returns_openai_client_when_key_present(self, mocker):
        mocker.patch(
            "batch_processing.batch_method.secrets_store.load_api_key",
            return_value="sk-test-fake-key",
        )
        mock_openai_cls = mocker.patch("batch_processing.batch_method.OpenAI")
        client = get_client()
        mock_openai_cls.assert_called_once_with(api_key="sk-test-fake-key")
        assert client is mock_openai_cls.return_value


# ---------------------------------------------------------------------------
# get_batch_results – mocked OpenAI client
# ---------------------------------------------------------------------------

def _make_response_line(custom_id: str, text_output: str, quote: str = "") -> str:
    """Build a single JSONL line matching the OpenAI batch output format."""
    return json.dumps(
        {
            "custom_id": custom_id,
            "response": {
                "body": {
                    "output": [{"content": [{"text": text_output}]}],
                    "metadata": {"quote": quote},
                }
            },
        }
    )


class TestGetBatchResults:
    def _setup_mock_client(self, mocker, output_file_id, file_content_bytes):
        mock_client = MagicMock()
        mocker.patch(
            "batch_processing.batch_method.get_client", return_value=mock_client
        )
        mock_status = MagicMock()
        mock_status.output_file_id = output_file_id
        mock_client.batches.retrieve.return_value = mock_status
        mock_client.files.content.return_value.content = file_content_bytes
        return mock_client, mock_status

    def test_successful_single_row(self, mocker):
        line = _make_response_line(
            "quote-00001", '{"label": "positive"}', quote="Great product!"
        )
        mock_client, _ = self._setup_mock_client(
            mocker, "file-123", (line + "\n").encode("utf-8")
        )
        mock_save = mocker.patch("batch_processing.batch_method.save_as_csv")

        get_batch_results("batch-001")

        mock_save.assert_called_once()
        df = mock_save.call_args[0][0]
        assert "label" in df.columns
        assert df["label"].iloc[0] == "positive"

    def test_multiple_rows_all_parsed(self, mocker):
        lines = "\n".join(
            [
                _make_response_line("quote-00001", '{"label": "positive"}', "Good."),
                _make_response_line("quote-00002", '{"label": "negative"}', "Bad."),
                _make_response_line("quote-00003", '{"label": "neutral"}', "OK."),
            ]
        )
        self._setup_mock_client(mocker, "file-234", (lines + "\n").encode("utf-8"))
        mock_save = mocker.patch("batch_processing.batch_method.save_as_csv")

        get_batch_results("batch-002")

        df = mock_save.call_args[0][0]
        assert len(df) == 3
        assert list(df["label"]) == ["positive", "negative", "neutral"]

    def test_malformed_row_excluded_from_results(self, mocker):
        """A row whose text cannot be parsed should be skipped (bad_rows), not crash."""
        bad_line = _make_response_line(
            "quote-00001", "COMPLETELY INVALID OUTPUT", "Some quote."
        )
        self._setup_mock_client(
            mocker, "file-345", (bad_line + "\n").encode("utf-8")
        )
        mock_save = mocker.patch("batch_processing.batch_method.save_as_csv")

        get_batch_results("batch-003")

        df = mock_save.call_args[0][0]
        assert len(df) == 0

    def test_mixed_good_and_bad_rows(self, mocker):
        """Only parsable rows end up in the saved DataFrame."""
        lines = "\n".join(
            [
                _make_response_line("quote-00001", '{"label": "positive"}', "Good."),
                _make_response_line("quote-00002", "NOT JSON AT ALL", "Bad."),
                _make_response_line("quote-00003", '{"label": "neutral"}', "OK."),
            ]
        )
        self._setup_mock_client(mocker, "file-456", (lines + "\n").encode("utf-8"))
        mock_save = mocker.patch("batch_processing.batch_method.save_as_csv")

        get_batch_results("batch-004")

        df = mock_save.call_args[0][0]
        assert len(df) == 2
        assert set(df["label"]) == {"positive", "neutral"}

    def test_repaired_truncated_row_gets_repair_note(self, mocker):
        """A repaired row should have a repair_note column in the output."""
        line = _make_response_line(
            "quote-00001", '{"label":"positive', "Truncated."
        )
        self._setup_mock_client(
            mocker, "file-567", (line + "\n").encode("utf-8")
        )
        mock_save = mocker.patch("batch_processing.batch_method.save_as_csv")

        get_batch_results("batch-005")

        df = mock_save.call_args[0][0]
        assert "repair_note" in df.columns

    def test_no_output_file_calls_handle_batch_fail(self, mocker):
        """When output_file_id is None, handle_batch_fail should be called."""
        mock_client = MagicMock()
        mocker.patch(
            "batch_processing.batch_method.get_client", return_value=mock_client
        )
        mock_status = MagicMock()
        mock_status.output_file_id = None
        mock_client.batches.retrieve.return_value = mock_status

        mock_fail = mocker.patch("batch_processing.batch_method.handle_batch_fail")

        get_batch_results("batch-failed")

        mock_fail.assert_called_once_with(mock_client, mock_status)

    def test_authentication_error_propagates(self, mocker):
        """If get_client raises (e.g., auth failure), the exception bubbles up."""
        mocker.patch(
            "batch_processing.batch_method.get_client",
            side_effect=Exception("OpenAI API key not configured"),
        )
        with pytest.raises(Exception, match="API key not configured"):
            get_batch_results("batch-auth-fail")

    def test_rate_limit_error_propagates(self, mocker):
        """A rate-limit exception from the API client bubbles up."""
        mock_client = MagicMock()
        mocker.patch(
            "batch_processing.batch_method.get_client", return_value=mock_client
        )
        mock_status = MagicMock()
        mock_status.output_file_id = "file-ratelimit"
        mock_client.batches.retrieve.return_value = mock_status
        mock_client.files.content.side_effect = Exception("Rate limit exceeded")

        with pytest.raises(Exception, match="Rate limit exceeded"):
            get_batch_results("batch-rate-limit")

    def test_connection_error_propagates(self, mocker):
        """A network/connection error from the API client bubbles up."""
        mock_client = MagicMock()
        mocker.patch(
            "batch_processing.batch_method.get_client", return_value=mock_client
        )
        mock_status = MagicMock()
        mock_status.output_file_id = "file-conn"
        mock_client.batches.retrieve.return_value = mock_status
        mock_client.files.content.side_effect = ConnectionError("Connection refused")

        with pytest.raises(ConnectionError):
            get_batch_results("batch-conn-error")

    def test_unexpected_response_schema_row_excluded(self, mocker):
        """A row with an unexpected but valid JSON schema still goes through _safe_parse."""
        # Valid JSON but not the expected schema – save_as_csv still called
        line = _make_response_line(
            "quote-00001", '{"unexpected_field": "value"}', "Quote."
        )
        self._setup_mock_client(
            mocker, "file-schema", (line + "\n").encode("utf-8")
        )
        mock_save = mocker.patch("batch_processing.batch_method.save_as_csv")

        get_batch_results("batch-schema")

        mock_save.assert_called_once()
        df = mock_save.call_args[0][0]
        # unexpected_field was parsed and included
        assert "unexpected_field" in df.columns

    def test_fenced_json_in_response(self, mocker):
        """A response with ```json fences is correctly parsed."""
        line = _make_response_line(
            "quote-00001",
            "```json\n{\"label\": \"positive\"}\n```",
            "Good.",
        )
        self._setup_mock_client(
            mocker, "file-fenced", (line + "\n").encode("utf-8")
        )
        mock_save = mocker.patch("batch_processing.batch_method.save_as_csv")

        get_batch_results("batch-fenced")

        df = mock_save.call_args[0][0]
        assert df["label"].iloc[0] == "positive"

    def test_empty_file_content_saves_empty_df(self, mocker):
        """An output file with no non-empty lines produces an empty DataFrame."""
        self._setup_mock_client(mocker, "file-empty", b"\n\n")
        mock_save = mocker.patch("batch_processing.batch_method.save_as_csv")

        get_batch_results("batch-empty")

        df = mock_save.call_args[0][0]
        assert len(df) == 0
