"""
OpenAI batch processing functionality for text classification.

This module handles the creation, monitoring, and result retrieval of OpenAI
batch processing jobs, driven by a core.task.Task instead of six hardcoded
per-tool flows. File import now happens once, before send_batch is called
(the Task Builder owns that), and carried columns are joined back in from a
local sidecar file rather than round-tripped through OpenAI request metadata.
"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
from openai import OpenAI

from batch_processing.batch_creation import generate_batch
from batch_processing.batch_error_handling import handle_batch_fail
from core.task import Task, build_request_params, validate_task
from file_handling.data_conversion import save_as_csv, to_long_df
from settings import secrets_store
from settings.user_config import get_setting, get_user_config_dir


def get_client() -> OpenAI:
    """
    Create and return an authenticated OpenAI client.

    Returns:
        Configured OpenAI client instance using stored API key

    Raises:
        Exception: If API key is not configured or invalid
    """
    api_key = secrets_store.load_api_key()
    if not api_key:
        raise Exception("OpenAI API key not configured. Please set it in Settings.")
    return OpenAI(api_key=api_key)


# ---------------------------------------------------------------------------
# Local sidecar: carries task.carry_columns through the batch round-trip.
# OpenAI's request metadata caps values at ~512 chars, which arbitrary carried
# columns (or even a single long quote) could exceed -- so carried data is
# kept locally, keyed by batch ID, and rejoined by row position on download.
# ---------------------------------------------------------------------------

def _sidecar_dir() -> Path:
    d = get_user_config_dir() / "sidecars"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sidecar_path(batch_id: str) -> Path:
    return _sidecar_dir() / f"{batch_id}.csv"


def _write_sidecar(batch_id: str, df: "pd.DataFrame", carry_columns: list[str]) -> None:
    if not carry_columns:
        return
    df[carry_columns].to_csv(_sidecar_path(batch_id), index=False)


def _read_sidecar(batch_id: str) -> "pd.DataFrame | None":
    path = _sidecar_path(batch_id)
    if not path.exists():
        return None
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _row_index_from_custom_id(custom_id: str | None) -> int | None:
    """'row-00001' -> 0 (matches sidecar's 0-based row order)."""
    if not custom_id:
        return None
    m = re.match(r"row-(\d+)$", custom_id)
    return int(m.group(1)) - 1 if m else None


def _task_type(task: Task) -> str:
    """Derive a display label for the batches table from the task's output shape.

    ponytail: precedence heuristic, not a formal classifier -- refine only if a
    task genuinely mixes output field types and the label needs to reflect that.
    """
    field_types = {f.type for f in task.output_fields}
    if "multi_choice" in field_types:
        return "multi-label"
    if "choice" in field_types:
        return "classification"
    if "text_list" in field_types:
        return "keyword extraction"
    return "free-text"


def _batch_metadata(task: Task, row_count: int, dataset: str | None) -> dict[str, str]:
    """Build the OpenAI batch metadata dict, including only the inference
    settings that actually apply to the chosen model (reuses build_request_params
    so the standard-vs-reasoning rule lives in exactly one place)."""
    params = build_request_params(task)
    md = {
        "model": task.model,
        "rows": str(row_count),
        "type": _task_type(task),
        "dataset": (dataset or "")[:64],
    }
    if "temperature" in params:
        md["temperature"] = str(params["temperature"])
    if "reasoning" in params:
        md["reasoning"] = params["reasoning"]["effort"]
    if "max_output_tokens" in params:
        md["max_output_tokens"] = str(params["max_output_tokens"])
    return md


def send_batch(task: Task, df: "pd.DataFrame", dataset: str | None = None) -> Any:
    """
    Submit a Task run against an already-imported DataFrame as a new batch job.

    Args:
        task: the built Task (prompt, lists, output fields, carried columns)
        df: the full imported table
        dataset: display name of the source dataset (e.g. the imported filename),
            recorded in batch metadata for the batches table

    Returns:
        OpenAI batch object containing job details and status

    Raises:
        TaskValidationError: if the task references unknown columns/lists
        Exception: if the API call fails
    """
    client = get_client()
    validate_task(task, list(df.columns))

    rows = df.to_dict(orient="records")
    batch_bytes = generate_batch(task, rows)

    batch_input_file = client.files.create(file=batch_bytes, purpose="batch")

    batch = client.batches.create(
        input_file_id=batch_input_file.id,
        endpoint="/v1/responses",
        completion_window="24h",
        metadata=_batch_metadata(task, len(rows), dataset),
    )

    _write_sidecar(batch.id, df, task.carry_columns)
    return batch


def get_batch_status(batch_id: str) -> Any:
    """
    Retrieve the current status of a batch processing job.

    Args:
        batch_id: Unique identifier for the batch job

    Returns:
        OpenAI batch status object with current job information
    """
    client = get_client()
    return client.batches.retrieve(batch_id)


def _safe_parse_model_text(s: str):
    t = s.strip()
    # strip ```json fences if present
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    try:
        return json.loads(t), None
    except Exception:
        # try to repair {"label":"disapproval
        m = re.match(r'^\{"label":"([^"}\n]+)', t)
        if m:
            return {"label": m.group(1)}, "Truncated JSON repaired"
        # try label: disapproval
        m2 = re.match(r'^\s*label\s*[:=]\s*"?([^"}\n]+)"?\s*$', t, flags=re.I)
        if m2:
            return {"label": m2.group(1)}, "Non-JSON label recovered"
        return None, f"Unparsable JSON text: {t[:80]}"


def get_batch_results(batch_id: str) -> None:
    """
    Download and save the results of a completed batch processing job.

    Retrieves the output file, parses each response, rejoins carried columns
    from the local sidecar (by row position), and prompts the user to save
    the combined table as a CSV.

    Args:
        batch_id: Unique identifier for the completed batch job

    Raises:
        Exception: If batch is not complete, results are malformed, or save fails
    """
    client = get_client()
    status = get_batch_status(batch_id)

    # Check if the batch has failed
    if status.output_file_id is None:
        handle_batch_fail(client, status)
        return

    # Download the output file content
    file_response = client.files.content(status.output_file_id).content
    results = [
        json.loads(line)
        for line in file_response.decode("utf-8").splitlines()
        if line.strip()
    ]

    sidecar = _read_sidecar(batch_id)  # row order matches the original request order

    responses, bad_rows = [], []

    for res in results:
        body = res['response']['body']
        text_output = body['output'][0]['content'][0]['text']
        parsed, note = _safe_parse_model_text(text_output)

        if parsed is None:
            bad_rows.append({
                "custom_id": res.get("custom_id"),
                "raw_text": text_output
            })
            continue

        combined = {"custom_id": res.get("custom_id")}
        if sidecar is not None:
            idx = _row_index_from_custom_id(res.get("custom_id"))
            if idx is not None and 0 <= idx < len(sidecar):
                combined.update(sidecar.iloc[idx].to_dict())
        combined.update(parsed)
        if note:
            combined["repair_note"] = note
        responses.append(combined)

    df = to_long_df(responses)
    save_as_csv(df)


def cancel_batch(batch_id: str) -> Any:
    """
    Cancel a running or queued batch processing job.

    Args:
        batch_id: Unique identifier for the batch job to cancel

    Returns:
        OpenAI batch object with updated status after cancellation
    """
    client = get_client()
    return client.batches.cancel(batch_id)


# Statuses that mean the batch is still active (used by the UI to decide
# whether to offer Cancel vs Download in the batches table).
ONGOING_STATUSES = {"validating", "in_progress", "cancelling", "finalizing"}


def list_batches() -> list[dict[str, str]]:
    """
    Retrieve recent batch processing jobs with their display metadata.

    Returns:
        List of dicts, most-recent-first, one per batch, with keys:
        id, status, type, dataset, model, rows, progress, created,
        temperature, reasoning, max_output_tokens.
        Metadata fields default to "" when a batch predates their introduction.

    Note:
        The number of batches returned is limited by config.max_batches.
        Timestamps are converted to the configured timezone.
    """
    limit = get_setting("max_batches", 4)
    client = get_client()
    tz = ZoneInfo(get_setting("time_zone", "UTC"))

    result = []
    for batch in client.batches.list(limit=limit):
        created_time = datetime.fromtimestamp(batch.created_at, tz)
        md = batch.metadata or {}

        rc = batch.request_counts
        progress = f"{rc.completed}/{rc.total}" if rc else ""
        if rc and rc.failed:
            progress += f" (+{rc.failed} failed)"

        result.append({
            "id": batch.id,
            "status": batch.status,
            "type": md.get("type", ""),
            "dataset": md.get("dataset", ""),
            "model": md.get("model", ""),
            "rows": md.get("rows", ""),
            "progress": progress,
            "created": created_time.strftime("%Y-%m-%d %H:%M"),
            "temperature": md.get("temperature", ""),
            "reasoning": md.get("reasoning", ""),
            "max_output_tokens": md.get("max_output_tokens", ""),
        })
    return result


def rerun_batch(batch_id: str, count: int = 1) -> list[str]:
    """
    Resubmit a batch with the exact same settings, `count` times.

    Reuses the original batch's retained input file and metadata directly --
    no Task or DataFrame needed -- so the new batches run the identical
    requests. The local sidecar (carried columns) is copied to each new batch
    id so results still rejoin correctly on download.

    Args:
        batch_id: the batch to rerun
        count: how many times to resubmit (default 1)

    Returns:
        List of new batch ids, in submission order.

    Raises:
        Exception: if the API call fails (e.g. the input file was deleted --
            ponytail: OpenAI retains input files for a limited time; a rerun
            of a very old batch may simply error, which is surfaced as-is).
    """
    client = get_client()
    orig = client.batches.retrieve(batch_id)

    new_ids = []
    for _ in range(count):
        new_batch = client.batches.create(
            input_file_id=orig.input_file_id,
            endpoint=orig.endpoint,
            completion_window=orig.completion_window or "24h",
            metadata=dict(orig.metadata or {}),
        )
        src = _sidecar_path(batch_id)
        if src.exists():
            shutil.copyfile(src, _sidecar_path(new_batch.id))
        new_ids.append(new_batch.id)
    return new_ids
