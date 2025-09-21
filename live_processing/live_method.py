import json
from settings import secrets_store
import tkinter as tk
import pandas as pd
from tkinter import messagebox, filedialog
from typing import Optional
from file_handling import csv_handling
from openai import OpenAI
from live_processing.response_calls import prompt_response
from file_handling.json_handling import build_schema

OPENAI_API_KEY = secrets_store.load_api_key()
client = OpenAI(api_key=OPENAI_API_KEY)


def send_live_call(parent: Optional[tk.Misc] = None):

    messagebox.showwarning("Warning", "Software will appear to freeze will running live processing. Please be patient. It can take a long time.")

    labels = csv_handling.import_csv(parent, "Select the labels CSV")
    quotes = csv_handling.import_csv(parent, "Select the quotes CSV")

    schema = build_schema(labels)

    responses = []
    for quote in quotes:
        response = json.loads(prompt_response(client, labels, quote, schema).output_text)
        responses.append(response["classifications"][0])
        # TODO: Add progress bar or status update

    output = pd.DataFrame(responses)

    file_path = filedialog.asksaveasfilename(
        title="Save classifications as CSV",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialfile="classifications.csv",
    )

    output.to_csv(file_path, index=False)

