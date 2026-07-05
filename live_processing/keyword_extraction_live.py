"""
Live text classification processing using OpenAI API.

This module provides real-time text classification functionality that processes
text snippets immediately using OpenAI's API, as opposed to batch processing.
This is useful for smaller datasets or when immediate results are needed.
"""

from typing import Optional
import tkinter as tk
from tkinter import messagebox
from pydantic import BaseModel, ValidationError, Field, ConfigDict
from file_handling.data_import import import_data
from file_handling.data_conversion import save_as_csv, to_long_df
from settings import config
from batch_processing.batch_method import get_client

# Progress UI lives in a separate module
from ui.progress_ui import ProgressController


def keyword_extraction_pipeline(parent: Optional[tk.Misc] = None):
    """
    Prompt for quotes CSVs, extract keywords from each quote,
    show progress, then save results to CSV.
    """
    try:
        client = get_client()
    except Exception as e:
        messagebox.showerror("API Key Required", str(e))
        return

    # Get quotes data
    from_import = import_data(parent, "Select the quotes data")
    if from_import is None:
        return  # user hit Cancel
    quotes, quotes_nickname = from_import

    class KeywordExtraction(BaseModel):
        id: int | None = None
        quote: str
        keywords: list[str] = Field(..., min_length=1)
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