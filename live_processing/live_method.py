import json
import config
OPENAI_API_KEY = config.OPENAI_API_KEY
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)
from live_processing.response_calls import prompt_response
from file_handling.csv_handling import import_csv
from file_handling.csv_handling import save_classifications_to_csv
from file_handling.json_handling import build_schema

def send_live_call(labels, quotes):
    schema = build_schema(labels)

    responses = []
    for quote in quotes:
        response = prompt_response(client, labels, quote, schema)
        responses.append(response)

    output = []
    for response in responses:
        data = json.loads(response.output_text)
        output.append(data)

    save_classifications_to_csv(output)

