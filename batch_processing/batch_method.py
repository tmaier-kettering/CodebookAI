import json
from tkinter import filedialog
import pandas as pd
from settings import config, secrets_store
from file_handling import csv_handling
from openai import OpenAI
from file_handling.json_handling import generate_batch_jsonl_bytes
from datetime import datetime, timezone
from zoneinfo import ZoneInfo



def get_client():
    return OpenAI(api_key=secrets_store.load_api_key())


def send_batch(root):
    client = get_client()

    labels = csv_handling.import_csv(root, "Select the labels CSV")
    quotes = csv_handling.import_csv(root, "Select the quotes CSV")

    batch_bytes = generate_batch_jsonl_bytes(labels, quotes)

    batch_input_file = client.files.create(
        file=batch_bytes,
        purpose="batch",
    )

    batch_input_file_id = batch_input_file.id

    batch = client.batches.create(
        input_file_id=batch_input_file_id,
        endpoint="/v1/responses",
        completion_window="24h",
        metadata={
            "description": "text classification"
        }
    )

    return batch


def get_batch_status(batch_id):
    client = get_client()
    return client.batches.retrieve(batch_id)


def get_batch_results(batch_id):
    client = get_client()
    status = get_batch_status(batch_id)
    file_response = client.files.content(status.output_file_id).content
    results = [
        json.loads(line)
        for line in file_response.decode("utf-8").splitlines()
        if line.strip()
    ]

    responses = []
    for res in results:
        response = json.loads(res['response']['body']['output'][1]['content'][0]['text'])
        responses.append(response["classifications"][0])

    output = pd.DataFrame(responses)

    file_path = filedialog.asksaveasfilename(
        title="Save classifications as CSV",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialfile="classifications.csv",
    )

    output.to_csv(file_path, index=False)


def cancel_batch(batch_id):
    client = get_client()
    return client.batches.cancel(batch_id)


def list_batches():
    limit = config.max_batches
    client = get_client()

    batches = client.batches.list(limit=limit)
    ongoing_batches = []
    done_batches = []
    for batch in batches:
        if batch.status == "validating" or batch.status == "in_progress" or batch.status == "cancelling" or batch.status == "finalizing":
            tuple_of_batch_data = (batch.id, batch.status, datetime.fromtimestamp(batch.created_at, ZoneInfo(config.time_zone)))
            ongoing_batches.append(tuple_of_batch_data)
        else:
            tuple_of_batch_data = (batch.id, batch.status, datetime.fromtimestamp(batch.created_at, ZoneInfo(config.time_zone)))
            done_batches.append(tuple_of_batch_data)

    return ongoing_batches, done_batches
