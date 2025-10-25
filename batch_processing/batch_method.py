"""
OpenAI batch processing functionality for text classification.

This module handles the creation, monitoring, and result retrieval of OpenAI
batch processing jobs. It provides functions to submit large collections of
text classification requests efficiently using OpenAI's batch API.
"""

import json
from batch_processing.batch_error_handling import handle_batch_fail
from file_handling.data_conversion import to_long_df, save_as_csv, join_datasets
from file_handling.data_import import import_data
from settings import config, secrets_store
from settings.user_config import get_setting
from openai import OpenAI
from batch_processing.batch_creation import generate_single_label_batch, generate_multi_label_batch, \
    generate_keyword_extraction_batch
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any
import re


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


def send_batch(root: Any, type: str) -> Any:
    """
    Create and submit a new batch processing job to OpenAI.

    This function prompts the user to select CSV files containing labels and
    text, generates a properly formatted batch request, and submits it to
    OpenAI's batch processing API.

    Args:
        root: Tkinter root window for file dialog ownership

    Returns:
        OpenAI batch object containing job details and status

    Raises:
        Exception: If file selection is cancelled, files are invalid, or API call fails
    """
    client = get_client()
    datasets = ()
    # Generate the JSONL batch file in memory
    if type == "single_label":
        # Get labels data
        from_import = import_data(root, "Select the labels data")
        if from_import is None:
            return  # user hit Cancel
        labels, labels_nickname = from_import

        # Get text data
        from_import = import_data(root, "Select the text data")
        if from_import is None:
            return  # user hit Cancel
        text, quotes_nickname = from_import

        batch_bytes = generate_single_label_batch(labels, text)
        datasets = (labels_nickname, quotes_nickname)
        joined_datasets = join_datasets(datasets)

    elif type == "multi_label":
        # Get labels data
        from_import = import_data(root, "Select the labels data")
        if from_import is None:
            return  # user hit Cancel
        labels, labels_nickname = from_import

        # Get text data
        from_import = import_data(root, "Select the text data")
        if from_import is None:
            return  # user hit Cancel
        text, quotes_nickname = from_import

        datasets = (labels_nickname, quotes_nickname)
        joined_datasets = join_datasets(datasets)
        batch_bytes = generate_multi_label_batch(labels, text)

    elif type == "keyword_extraction":
        # Get text data
        from_import = import_data(root, "Select the text data")
        if from_import is None:
            return  # user hit Cancel
        text, text_nickname = from_import

        joined_datasets = join_datasets(text_nickname)
        batch_bytes = generate_keyword_extraction_batch(text)
    else:
        raise ValueError(f"Unknown batch type: {type}")

    # Upload the batch file to OpenAI
    batch_input_file = client.files.create(
        file=batch_bytes,
        purpose="batch",
    )

    batch_input_file_id = batch_input_file.id

    # Create the batch processing job
    batch = client.batches.create(
        input_file_id=batch_input_file_id,
        endpoint="/v1/responses",
        completion_window="24h",
        metadata={
            "model": get_setting("model", "gpt-4o"),
            "type": type,
            "dataset(s)": joined_datasets
        }
    )

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


    # Extract classification results from the API responses
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

    This function retrieves the output file from a completed batch job,
    parses the classification results, and prompts the user to save them
    as a CSV file.

    Args:
        batch_id: Unique identifier for the completed batch job

    Raises:
        Exception: If batch is not complete, results are malformed, or save fails

    Note:
        Results are automatically saved as a DataFrame with columns for
        quote, label, and confidence from the classification response.
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

    responses, bad_rows = [], []

    for res in results:
        body = res['response']['body']
        text_output = body['output'][0]['content'][0]['text']
        parsed, note = _safe_parse_model_text(text_output)

        if parsed is None:
            bad_rows.append({
                "custom_id": res.get("custom_id"),
                "quote": body.get("metadata", {}).get("quote", ""),
                "raw_text": text_output
            })
            continue

        metadata = body.get('metadata', {})
        combined = {"custom_id": res.get("custom_id"), **metadata, **parsed}
        if note:
            combined["repair_note"] = note
        responses.append(combined)

    # Now continue with your DF creation
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


def list_batches():
    """
    Retrieve and categorize recent batch processing jobs.

    This function fetches the most recent batch jobs and separates them into
    ongoing (active) and completed batches based on their status.

    Returns:
        Tuple of (ongoing_batches, done_batches) where each is a list of tuples
        containing (batch_id, status, created_timestamp)

    Note:
        The number of batches returned is limited by config.max_batches.
        Timestamps are converted to the configured timezone.
    """
    limit = get_setting("max_batches", 4)
    client = get_client()

    batches = client.batches.list(limit=limit)
    ongoing_batches = []
    done_batches = []

    # Categorize batches by status
    ongoing_statuses = {"validating", "in_progress", "cancelling", "finalizing"}

    for batch in batches:
        # Convert timestamp to configured timezone
        created_time = datetime.fromtimestamp(batch.created_at, ZoneInfo(get_setting("time_zone", "UTC")))

        md = (batch.metadata or {})
        tuple_of_batch_data = (
            batch.id,
            batch.status,
            created_time,
            md.get("model", ""),
            md.get("type", ""),
            md.get("dataset(s)", "")
        )

        if batch.status in ongoing_statuses:
            ongoing_batches.append(tuple_of_batch_data)
        else:
            done_batches.append(tuple_of_batch_data)

    return ongoing_batches, done_batches
