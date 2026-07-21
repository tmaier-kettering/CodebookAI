"""
Tests for batch_processing/batch_method.py

Covers:
- _safe_parse_model_text: valid JSON, fenced JSON, truncated JSON, non-JSON,
  completely unparsable, empty string, whitespace
- get_client: missing API key raises, valid key returns client
- send_batch: validates the task before calling the API, writes a sidecar
  for carried columns, skips the sidecar when nothing is carried
- get_batch_results: successful response, malformed rows, missing output
  file, and rejoining carried columns from the local sidecar
- Authentication failures, rate limit errors, timeout/connection errors
"""

import json
from unittest.mock import MagicMock

import pandas as pd
import pytest

from batch_processing.batch_method import (
    _read_sidecar,
    _row_index_from_custom_id,
    _safe_parse_model_text,
    _sidecar_path,
    _task_type,
    get_batch_results,
    get_client,
    rerun_batch,
    send_batch,
)
from core.task import OutputField, Task, TaskList, TaskValidationError


@pytest.fixture(autouse=True)
def isolated_config_dir(tmp_path, monkeypatch):
    """Redirect the sidecar directory to a temp dir (mirrors test_settings.py)."""
    config_dir = tmp_path / "CodebookAI"
    config_dir.mkdir()
    monkeypatch.setattr("batch_processing.batch_method.get_user_config_dir", lambda: config_dir)
    yield config_dir


def _single_label_task(carry_columns=()) -> Task:
    return Task(
        prompt="Allowed: {labels}\nQuote: {quote}",
        lists={"labels": TaskList(["positive", "negative", "neutral"])},
        output_fields=[OutputField(name="label", type="choice", list_ref="labels")],
        carry_columns=list(carry_columns),
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
# _row_index_from_custom_id
# ---------------------------------------------------------------------------

class TestRowIndexFromCustomId:
    def test_first_row(self):
        assert _row_index_from_custom_id("row-00001") == 0

    def test_later_row(self):
        assert _row_index_from_custom_id("row-00042") == 41

    def test_none_returns_none(self):
        assert _row_index_from_custom_id(None) is None

    def test_malformed_returns_none(self):
        assert _row_index_from_custom_id("not-a-row-id") is None


# ---------------------------------------------------------------------------
# send_batch
# ---------------------------------------------------------------------------

class TestSendBatch:
    def _mock_client(self, mocker):
        mock_client = MagicMock()
        mocker.patch("batch_processing.batch_method.get_client", return_value=mock_client)
        mock_client.files.create.return_value.id = "file-abc"
        mock_client.batches.create.return_value.id = "batch-abc"
        return mock_client

    def test_invalid_task_raises_before_calling_api(self, mocker):
        mock_client = self._mock_client(mocker)
        task = Task(prompt="{ghost}", output_fields=[])  # unknown placeholder, no output fields
        df = pd.DataFrame({"quote": ["hi"]})
        with pytest.raises(TaskValidationError):
            send_batch(task, df)
        mock_client.files.create.assert_not_called()

    def test_valid_task_uploads_and_creates_batch(self, mocker):
        mock_client = self._mock_client(mocker)
        df = pd.DataFrame({"quote": ["a", "b"]})
        batch = send_batch(_single_label_task(), df)
        mock_client.files.create.assert_called_once()
        mock_client.batches.create.assert_called_once()
        assert batch.id == "batch-abc"

    def test_carried_columns_written_to_sidecar(self, mocker, isolated_config_dir):
        self._mock_client(mocker)
        df = pd.DataFrame({"quote": ["a", "b"], "quote_id": ["R001", "R002"]})
        send_batch(_single_label_task(carry_columns=["quote_id"]), df)

        sidecar = _read_sidecar("batch-abc")
        assert sidecar is not None
        assert list(sidecar["quote_id"]) == ["R001", "R002"]

    def test_no_carried_columns_skips_sidecar(self, mocker, isolated_config_dir):
        self._mock_client(mocker)
        df = pd.DataFrame({"quote": ["a"]})
        send_batch(_single_label_task(carry_columns=[]), df)
        assert not _sidecar_path("batch-abc").exists()

    def test_metadata_includes_type_and_dataset(self, mocker):
        mock_client = self._mock_client(mocker)
        df = pd.DataFrame({"quote": ["a", "b"]})
        send_batch(_single_label_task(), df, dataset="reviews")

        md = mock_client.batches.create.call_args.kwargs["metadata"]
        assert md["type"] == "classification"
        assert md["dataset"] == "reviews"
        assert md["rows"] == "2"

    def test_metadata_dataset_blank_when_not_given(self, mocker):
        mock_client = self._mock_client(mocker)
        df = pd.DataFrame({"quote": ["a"]})
        send_batch(_single_label_task(), df)

        md = mock_client.batches.create.call_args.kwargs["metadata"]
        assert md["dataset"] == ""

    def test_metadata_standard_model_has_temperature_not_reasoning(self, mocker):
        mock_client = self._mock_client(mocker)
        df = pd.DataFrame({"quote": ["a"]})
        task = _single_label_task()
        task.model = "gpt-4o-mini"
        task.temperature = 0.5
        task.reasoning_effort = "high"  # ignored: not a reasoning model
        send_batch(task, df)

        md = mock_client.batches.create.call_args.kwargs["metadata"]
        assert md["temperature"] == "0.5"
        assert "reasoning" not in md

    def test_metadata_reasoning_model_has_reasoning_not_temperature(self, mocker):
        mock_client = self._mock_client(mocker)
        df = pd.DataFrame({"quote": ["a"]})
        task = _single_label_task()
        task.model = "o3"
        task.temperature = 0.5  # ignored: reasoning models don't take temperature
        task.reasoning_effort = "high"
        send_batch(task, df)

        md = mock_client.batches.create.call_args.kwargs["metadata"]
        assert md["reasoning"] == "high"
        assert "temperature" not in md


# ---------------------------------------------------------------------------
# _task_type
# ---------------------------------------------------------------------------

class TestTaskType:
    def _task_with(self, field_type: str) -> Task:
        list_ref = "labels" if field_type in ("choice", "multi_choice") else None
        return Task(
            prompt="x",
            lists={"labels": TaskList(["a", "b"])} if list_ref else {},
            output_fields=[OutputField(name="out", type=field_type, list_ref=list_ref)],
        )

    def test_multi_choice_is_multi_label(self):
        assert _task_type(self._task_with("multi_choice")) == "multi-label"

    def test_choice_is_classification(self):
        assert _task_type(self._task_with("choice")) == "classification"

    def test_text_list_is_keyword_extraction(self):
        assert _task_type(self._task_with("text_list")) == "keyword extraction"

    def test_free_text_is_free_text(self):
        assert _task_type(self._task_with("free_text")) == "free-text"


# ---------------------------------------------------------------------------
# rerun_batch
# ---------------------------------------------------------------------------

class TestRerunBatch:
    def _mock_client_for_rerun(self, mocker):
        mock_client = MagicMock()
        mocker.patch("batch_processing.batch_method.get_client", return_value=mock_client)
        orig = MagicMock()
        orig.input_file_id = "file-orig"
        orig.endpoint = "/v1/responses"
        orig.completion_window = "24h"
        orig.metadata = {"model": "gpt-4o-mini", "type": "classification"}
        mock_client.batches.retrieve.return_value = orig
        mock_client.batches.create.side_effect = [
            MagicMock(id="batch-rerun-1"), MagicMock(id="batch-rerun-2"),
        ]
        return mock_client

    def test_reruns_reuse_input_file_and_metadata(self, mocker):
        mock_client = self._mock_client_for_rerun(mocker)
        new_ids = rerun_batch("batch-orig", count=2)

        assert new_ids == ["batch-rerun-1", "batch-rerun-2"]
        assert mock_client.batches.create.call_count == 2
        for call in mock_client.batches.create.call_args_list:
            assert call.kwargs["input_file_id"] == "file-orig"
            assert call.kwargs["metadata"] == {"model": "gpt-4o-mini", "type": "classification"}

    def test_default_count_is_one(self, mocker):
        mock_client = self._mock_client_for_rerun(mocker)
        new_ids = rerun_batch("batch-orig")
        assert new_ids == ["batch-rerun-1"]

    def test_sidecar_copied_to_each_new_batch(self, mocker, isolated_config_dir):
        self._mock_client_for_rerun(mocker)
        df = pd.DataFrame({"quote_id": ["R001", "R002"]})
        df.to_csv(_sidecar_path("batch-orig"), index=False)

        rerun_batch("batch-orig", count=2)

        for new_id in ("batch-rerun-1", "batch-rerun-2"):
            sidecar = _read_sidecar(new_id)
            assert sidecar is not None
            assert list(sidecar["quote_id"]) == ["R001", "R002"]

    def test_no_sidecar_is_fine(self, mocker, isolated_config_dir):
        self._mock_client_for_rerun(mocker)
        new_ids = rerun_batch("batch-orig", count=1)
        assert new_ids == ["batch-rerun-1"]
        assert _read_sidecar("batch-rerun-1") is None


# ---------------------------------------------------------------------------
# get_batch_results – mocked OpenAI client
# ---------------------------------------------------------------------------

def _make_response_line(custom_id: str, text_output: str) -> str:
    """Build a single JSONL line matching the OpenAI batch output format.
    Request metadata is no longer echoed (dropped in favor of the local
    sidecar), so the response body carries no 'metadata' key."""
    return json.dumps(
        {
            "custom_id": custom_id,
            "response": {
                "body": {
                    "output": [{"content": [{"text": text_output}]}],
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
        line = _make_response_line("row-00001", '{"label": "positive"}')
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
                _make_response_line("row-00001", '{"label": "positive"}'),
                _make_response_line("row-00002", '{"label": "negative"}'),
                _make_response_line("row-00003", '{"label": "neutral"}'),
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
        bad_line = _make_response_line("row-00001", "COMPLETELY INVALID OUTPUT")
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
                _make_response_line("row-00001", '{"label": "positive"}'),
                _make_response_line("row-00002", "NOT JSON AT ALL"),
                _make_response_line("row-00003", '{"label": "neutral"}'),
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
        line = _make_response_line("row-00001", '{"label":"positive')
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
        line = _make_response_line("row-00001", '{"unexpected_field": "value"}')
        self._setup_mock_client(
            mocker, "file-schema", (line + "\n").encode("utf-8")
        )
        mock_save = mocker.patch("batch_processing.batch_method.save_as_csv")

        get_batch_results("batch-schema")

        mock_save.assert_called_once()
        df = mock_save.call_args[0][0]
        assert "unexpected_field" in df.columns

    def test_fenced_json_in_response(self, mocker):
        """A response with ```json fences is correctly parsed."""
        line = _make_response_line("row-00001", "```json\n{\"label\": \"positive\"}\n```")
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

    def test_carried_columns_rejoined_from_sidecar(self, mocker, isolated_config_dir, tmp_path):
        """Carried columns written by send_batch are rejoined by row position
        when results come back -- this is the quote_id pass-through case."""
        from batch_processing.batch_method import _sidecar_dir
        sidecar_df = pd.DataFrame({"quote_id": ["R001", "R002"]})
        sidecar_df.to_csv(_sidecar_dir() / "batch-sidecar.csv", index=False)

        lines = "\n".join(
            [
                _make_response_line("row-00001", '{"label": "positive"}'),
                _make_response_line("row-00002", '{"label": "negative"}'),
            ]
        )
        self._setup_mock_client(mocker, "file-sidecar", (lines + "\n").encode("utf-8"))
        mock_save = mocker.patch("batch_processing.batch_method.save_as_csv")

        get_batch_results("batch-sidecar")

        df = mock_save.call_args[0][0]
        assert list(df["quote_id"]) == ["R001", "R002"]
        assert list(df["label"]) == ["positive", "negative"]

    def test_no_sidecar_file_still_produces_results(self, mocker):
        """If no sidecar was ever written (no carried columns), results
        still parse fine -- carried columns are simply absent."""
        line = _make_response_line("row-00001", '{"label": "positive"}')
        self._setup_mock_client(mocker, "file-nosidecar", (line + "\n").encode("utf-8"))
        mock_save = mocker.patch("batch_processing.batch_method.save_as_csv")

        get_batch_results("batch-nosidecar-xyz")

        df = mock_save.call_args[0][0]
        assert df["label"].iloc[0] == "positive"
