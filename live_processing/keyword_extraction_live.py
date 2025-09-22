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
from file_handling.data_conversion import save_as_csv, to_long_df
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


def keyword_extraction_pipeline(parent: Optional[tk.Misc] = None):
    """
    Prompt for quotes CSVs, extract keywords from each quote,
    show progress, then save results to CSV.
    """
    # Get quotes CSV
    quotes = import_csv(parent, "Select the quotes CSV")
    if quotes is None:
        return  # user hit Cancel

    class KeywordExtraction(BaseModel):
        id: int | None = None
        quote: str
        keywords: list[str] = Field(..., min_items=1)
        model_config = ConfigDict()

    total = len(quotes)

    progress = ProgressController.open(parent=parent, total_count=total, title="Processing quotes…")

    results: list[KeywordExtraction] = []
    try:
        for idx, q in enumerate(quotes, start=1):
            try:
                resp = client.responses.parse(
                    model=config.model,
                    input=[{"role": "system", "content": "You are an expert at structured data extraction."},
                        {"role": "user", "content": f"Extract the keywords from this quote: {q}"}],
                    text_format=KeywordExtraction,
                )
                decision = resp.output_parsed
                row = KeywordExtraction(
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