"""
Live text classification processing using OpenAI API.

This module provides real-time text classification functionality that processes
text snippets immediately using OpenAI's API, as opposed to batch processing.
This is useful for smaller datasets or when immediate results are needed.
"""

from typing import Optional
import tkinter as tk
from pydantic import BaseModel, ValidationError, Field, ConfigDict
from openai import OpenAI
from file_handling.csv_handling import import_csv
from file_handling.data_conversion import make_str_enum, save_as_csv, to_long_df
from settings import secrets_store, config

# Progress UI lives in a separate module
from ui.progress_ui import ProgressController

# Initialize OpenAI client with stored API key
try:
    OPENAI_API_KEY = secrets_store.load_api_key()
    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    OPENAI_API_KEY = None
    client = None


def single_label_pipeline(parent: Optional[tk.Misc] = None):
    """
    Prompt for labels/quotes CSVs, classify each quote with exactly one label,
    show progress, then save results to CSV.
    """
    # Get labels CSV; if user cancels, just exit cleanly
    label_values, labels_filename = import_csv(parent, "Select the labels CSV")
    if label_values is None:
        return  # user hit Cancel
    labels = make_str_enum("Label", label_values)

    # Get quotes CSV
    quotes, quotes_filename = import_csv(parent, "Select the quotes CSV")
    if quotes is None:
        return  # user hit Cancel

    class LabeledQuote(BaseModel):
        id: int | None = None
        quote: str
        label: labels  # STRICT: must be one of labels
        confidence: float = Field(..., ge=0, le=1)
        model_config = ConfigDict(use_enum_values=True, extra='forbid')


    total = len(quotes)

    progress = ProgressController.open(parent=parent, total_count=total, title="Processing quotes…")

    results: list[LabeledQuote] = []
    try:
        for idx, q in enumerate(quotes, start=1):
            try:
                resp = client.responses.parse(
                    model=config.model,
                    input=[{
                        "role": "user",
                        "content": (
                            f"Label this quote with exactly one emotion from the allowed set.\n"
                            f"Quote: {q}"
                        ),
                    }],
                    text_format=LabeledQuote,
                )
                decision = resp.output_parsed
                row = LabeledQuote(
                    id=idx,
                    quote=q,
                    **decision.model_dump(exclude={'id', 'quote'})  # <- prevents duplicate kwargs
                )
                results.append(row)
            except ValidationError as ve:
                print(f"[VALIDATION ERROR] {str(q)[:60]}... -> {ve}")
            except Exception as e:
                print(f"[API ERROR] {str(q)[:60]}... -> {e}")
            finally:
                progress.update(idx, message=f"Processed {idx} of {total} quotes")
    finally:
        progress.close()

    df = to_long_df(results)
    save_as_csv(df)