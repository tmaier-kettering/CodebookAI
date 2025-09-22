"""
Live text classification processing using OpenAI API.

This module provides real-time text classification functionality that processes
text snippets immediately using OpenAI's API, as opposed to batch processing.
This is useful for smaller datasets or when immediate results are needed.
"""

import json

from pydantic import BaseModel, ValidationError, Field, ConfigDict

from file_handling.csv_handling import import_csv, import_csv_from_file
from file_handling.data_conversion import make_str_enum, save_as_csv
from settings import secrets_store, config
import tkinter as tk
import pandas as pd
from tkinter import messagebox, filedialog
from typing import Optional, List
from file_handling import csv_handling
from openai import OpenAI
from live_processing.response_calls import prompt_response
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

    results: list[LabeledQuote] = []

    # TODO: Open Progress Bar window here

    # Process each quote individually
    for q in quotes:
        try:
            resp = client.responses.parse(
                model=config.model,
                input=[{"role": "user", "content": f"Label this quote with exactly one emotion: {q}"}],
                text_format=LabeledQuote,
            )
            results.append(resp.output_parsed)  # Validated LabeledQuote
        except ValidationError as ve:
            # Model tried to output something outside your enum (or wrong shape)
            print(f"[VALIDATION ERROR] {q[:60]}... -> {ve}")
        except Exception as e:
            # Transport/SDK errors, etc.
            print(f"[API ERROR] {q[:60]}... -> {e}")

        # TODO: Update Progress Bar here

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


def process_live_classification(labels_file: str, quotes_file: str, is_multi_label: bool, parent: Optional[tk.Misc] = None):
    """
    Process text classification using files specified directly.
    
    This function processes classification using the selected files and mode,
    without showing file selection dialogs.
    
    Args:
        labels_file: Path to CSV file containing labels
        quotes_file: Path to CSV file containing quotes to classify
        is_multi_label: True for multi-label, False for single-label processing
        parent: Optional Tkinter parent widget for dialog ownership
        
    Raises:
        ValueError: If files cannot be read or are empty
        Exception: If API processing fails
    """
    try:
        # Read the CSV files directly
        labels_data = import_csv_from_file(labels_file, has_headers=False)
        quotes_data = import_csv_from_file(quotes_file, has_headers=False)
        
        if not labels_data:
            raise ValueError("Labels file is empty or contains no valid data")
        if not quotes_data:
            raise ValueError("Quotes file is empty or contains no valid data")
            
        # Create enum from labels
        labels = make_str_enum("Label", labels_data)
        
        if is_multi_label:
            _process_multi_label_with_data(labels, quotes_data)
        else:
            _process_single_label_with_data(labels, quotes_data)
            
    except Exception as e:
        if parent:
            messagebox.showerror("Processing Error", f"Failed to process files:\n{str(e)}", parent=parent)
        else:
            print(f"Processing Error: {e}")
        raise


def _process_single_label_with_data(labels, quotes_data: List[str]):
    """Process single-label classification with provided data."""
    if not client:
        raise ValueError("OpenAI API client not initialized. Please check your API key in settings.")
    
    class LabeledQuote(BaseModel):
        quote: str
        label: labels  # STRICT: must be one of labels
        confidence: float = Field(..., ge=0, le=1)  # Confidence score between 0 and 1
        model_config = ConfigDict(use_enum_values=True)

    results: list[LabeledQuote] = []

    # Process each quote individually
    for q in quotes_data:
        try:
            resp = client.responses.parse(
                model=config.model,
                input=[{"role": "user", "content": f"Label this quote with exactly one emotion: {q}"}],
                text_format=LabeledQuote,
            )
            results.append(resp.output_parsed)  # Validated LabeledQuote
        except ValidationError as ve:
            print(f"[VALIDATION ERROR] {q[:60]}... -> {ve}")
        except Exception as e:
            print(f"[API ERROR] {q[:60]}... -> {e}")

    # Convert results to DataFrame and save as CSV
    rows = [m.model_dump() for m in results]
    df = pd.DataFrame(rows)
    save_as_csv(df)


def _process_multi_label_with_data(labels, quotes_data: List[str]):
    """Process multi-label classification with provided data."""
    if not client:
        raise ValueError("OpenAI API client not initialized. Please check your API key in settings.")
    
    class LabeledQuoteMulti(BaseModel):
        quote: str
        label: List[labels] = Field(..., min_items=1)
        confidence: float = Field(..., ge=0, le=1)  # Confidence score between 0 and 1
        model_config = ConfigDict(use_enum_values=True)

    # Process each quote individually
    results: list[LabeledQuoteMulti] = []
    for q in quotes_data:
        try:
            resp = client.responses.parse(
                model=config.model,
                input=[{
                    "role": "user",
                    "content": (
                        "Label this quote with labels from the allowed set only. "
                        f"Allowed: {', '.join(labels)}\\nQuote: {q}"
                    ),
                }],
                text_format=LabeledQuoteMulti,
            )
            results.append(resp.output_parsed)
        except ValidationError as ve:
            print(f"[VALIDATION ERROR] {q[:60]}... -> {ve}")
        except Exception as e:
            print(f"[API ERROR] {q[:60]}... -> {e}")

    # Convert results to DataFrame and save as CSV
    rows = [m.model_dump() for m in results]
    df = pd.DataFrame(rows)
    save_as_csv(df)
