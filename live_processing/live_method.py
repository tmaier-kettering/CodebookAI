"""
Live text classification processing using OpenAI API.

This module provides real-time text classification functionality that processes
text snippets immediately using OpenAI's API, as opposed to batch processing.
This is useful for smaller datasets or when immediate results are needed.
"""

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

# Initialize OpenAI client with stored API key
try:
    OPENAI_API_KEY = secrets_store.load_api_key()
    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    # Handle cases where keyring is not available (testing environments)
    OPENAI_API_KEY = None
    client = None


def send_live_call(parent: Optional[tk.Misc] = None) -> None:
    """
    Process text classification requests in real-time using OpenAI API.
    
    This function prompts the user to select CSV files containing labels and
    quotes, then processes each quote individually through the OpenAI API,
    collecting results and saving them as a CSV file.
    
    Args:
        parent: Optional Tkinter parent widget for dialog ownership
        
    Warning:
        This function processes requests synchronously and may take considerable
        time for large datasets. The UI will appear frozen during processing.
        
    Note:
        Results are saved as a CSV file with columns for quote, label, and confidence.
        Progress indication is currently limited (TODO: add progress bar).
    """
    # Warn user about potential UI freezing
    messagebox.showwarning(
        "Warning", 
        "Software will appear to freeze while running live processing. "
        "Please be patient. It can take a long time."
    )

    # Get input data from user-selected CSV files
    labels = csv_handling.import_csv(parent, "Select the labels CSV")
    quotes = csv_handling.import_csv(parent, "Select the quotes CSV")

    # Validate inputs
    if not labels or not quotes:
        messagebox.showerror("Error", "Both labels and quotes are required.")
        return

    # Build JSON schema for structured responses
    schema = build_schema(labels)

    # Process each quote individually
    responses = []
    for quote in quotes:
        try:
            response = json.loads(prompt_response(client, labels, quote, schema).output_text)
            responses.append(response["classifications"][0])
            # TODO: Add progress bar or status update for better UX
        except Exception as e:
            messagebox.showerror("Processing Error", f"Failed to process quote: {quote}\nError: {str(e)}")
            return

    # Convert results to DataFrame for CSV export
    output = pd.DataFrame(responses)

    # Prompt user to save results
    file_path = filedialog.asksaveasfilename(
        title="Save classifications as CSV",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialfile="classifications.csv",
    )

    if file_path:  # Only save if user didn't cancel
        output.to_csv(file_path, index=False)
        messagebox.showinfo("Success", f"Classifications saved to {file_path}")
    else:
        messagebox.showinfo("Cancelled", "Save operation cancelled.")

