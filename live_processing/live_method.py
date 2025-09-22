"""
Live text classification processing using OpenAI API.

This module provides real-time text classification functionality that processes
text snippets immediately using OpenAI's API, as opposed to batch processing.
This is useful for smaller datasets or when immediate results are needed.
"""

import json

from pydantic import BaseModel, ValidationError, Field, ConfigDict

from file_handling.csv_handling import import_csv
from file_handling.data_conversion import make_str_enum, save_as_csv
from settings import secrets_store, config
import tkinter as tk
import pandas as pd
from tkinter import messagebox, filedialog
from typing import Optional, List
from file_handling import csv_handling
from openai import OpenAI
from live_processing.response_calls import prompt_response, parse_quotes
from file_handling.json_handling import build_schema

# Initialize OpenAI client with stored API key
try:
    OPENAI_API_KEY = secrets_store.load_api_key()
    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    # Handle cases where keyring is not available (testing environments)
    OPENAI_API_KEY = None
    client = None


def single_label_pipeline(parent: Optional[tk.Misc] = None):
    """
    Process text classification requests in real-time using OpenAI API.

    This function prompts the user to select CSV files containing labels and
    quotes, then processes each quote individually through the OpenAI API,
    collecting results and saving them as a CSV file.

    Args:
        parent: Optional Tkinter parent widget for dialog ownership

    Warning:
        This function processes requests synchronously and may take considerable
        time for large datasets. You cannot interact with the UI during processing.
    """

    labels = make_str_enum("Label", import_csv(parent, "Select the labels CSV"))

    class LabeledQuote(BaseModel):
        quote: str
        label: labels  # STRICT: must be one of labels
        confidence: float = Field(..., ge=0, le=1)  # Confidence score between 0 and 1
        model_config = ConfigDict(use_enum_values=True)

    quotes = import_csv(parent, "Select the quotes CSV")

    results = parse_quotes(LabeledQuote, quotes, "Label this quote with exactly one emotion from the allowed set.\nQuote: {q}")

    # Convert results to DataFrame and save as CSV
    rows = [m.model_dump() for m in results]
    df = pd.DataFrame(rows)
    save_as_csv(df)


def multi_label_pipeline(parent: Optional[tk.Misc] = None):
    """
        Process text classification requests in real-time using OpenAI API.

        This function prompts the user to select CSV files containing labels and
        quotes, then processes each quote individually through the OpenAI API,
        collecting results and saving them as a CSV file.

        Args:
            parent: Optional Tkinter parent widget for dialog ownership

        Warning:
            This function processes requests synchronously and may take considerable
            time for large datasets. You cannot interact with the UI during processing.
        """

    labels = make_str_enum("Label", import_csv(parent, "Select the labels CSV"))

    class LabeledQuoteMulti(BaseModel):
        quote: str
        label: List[labels] = Field(..., min_items=1)
        confidence: float = Field(..., ge=0, le=1)  # Confidence score between 0 and 1
        model_config = ConfigDict(use_enum_values=True)

    quotes = import_csv(parent, "Select the quotes CSV")

    # TODO: Open Progress Bar window here

    # Process each quote individually
    results: list[LabeledQuoteMulti] = []
    for q in quotes:
        try:
            resp = client.responses.parse(
                model=config.model,
                input=[{
                    "role": "user",
                    "content": (
                        "Label this quote with labels from the allowed set only. "
                        f"Allowed: {', '.join(labels)}\nQuote: {q}"
                    ),
                }],
                text_format=LabeledQuoteMulti,
            )
            results.append(resp.output_parsed)
        except ValidationError as ve:
            print(f"[VALIDATION ERROR] {q[:60]}... -> {ve}")
        except Exception as e:
            print(f"[API ERROR] {q[:60]}... -> {e}")

        # TODO: Update Progress Bar here

    # Convert results to DataFrame and save as CSV
    rows = [m.model_dump() for m in results]
    df = pd.DataFrame(rows)
    save_as_csv(df)
