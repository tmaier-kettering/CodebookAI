import json
from tkinter import messagebox
import tkinter as tk
from typing import Optional

import config
from file_handling import csv_handling
OPENAI_API_KEY = config.OPENAI_API_KEY
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)
from live_processing.response_calls import prompt_response
from file_handling.csv_handling import import_csv, _ensure_parent
from file_handling.csv_handling import save_classifications_to_csv
from file_handling.json_handling import build_schema

def send_live_call(parent: Optional[tk.Misc] = None):
    owner, created_root = _ensure_parent(parent)

    messagebox.showwarning("Warning", "Software will appear to freeze will running live processing. Please be patient. It can take a long time.")

    labels = csv_handling.import_csv(parent, "Select the labels CSV")
    quotes = csv_handling.import_csv(parent, "Select the quotes CSV")

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

