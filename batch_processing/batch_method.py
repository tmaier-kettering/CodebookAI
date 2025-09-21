import config
OPENAI_API_KEY = config.OPENAI_API_KEY
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)
from file_handling.json_handling import generate_batch_jsonl_bytes
from file_handling.csv_handling import import_csv, save_classifications_csv_from_content_bytes


# Create your batch input file
def send_batch(labels, quotes):
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


def get_batch_status(batch):
    return client.batches.retrieve(batch.id)


def get_batch_results(batch):
    status = get_batch_status(batch)
    file_response = client.files.content(status.output_file_id).content
    save_classifications_csv_from_content_bytes(file_response)


def cancel_batch(batch_id):
    return client.batches.cancel(batch_id)


def list_batches(limit=20):
    return client.batches.list(limit=limit)

