"""
Live (synchronous, one-request-per-row) execution of a core.task.Task.

Replaces single_label_live.py / multi_label_live.py / keyword_extraction_live.py
-- one loop now handles any task shape, including combinations none of the old
tools could do alone (e.g. a label AND keywords AND a free-text reason in the
same run).
"""

from typing import Any, Optional

import tkinter as tk
from tkinter import messagebox

import pandas as pd
from pydantic import ValidationError

from core.task import Task, build_output_model, build_request_params, render_prompt, validate_task
from file_handling.data_conversion import save_as_csv, to_long_df
from batch_processing.batch_method import get_client

from ui.progress_ui import ProgressController


def run_task_live(parent: Optional[tk.Misc], task: Task, df: "pd.DataFrame") -> None:
    """
    Run `task` against every row of `df` synchronously, showing progress, then
    prompt to save the results (carried columns + output fields) as CSV.
    """
    try:
        client = get_client()
    except Exception as e:
        messagebox.showerror("API Key Required", str(e))
        return

    validate_task(task, list(df.columns))
    output_model = build_output_model(task)
    request_params = build_request_params(task)

    rows = df.to_dict(orient="records")
    total = len(rows)
    progress = ProgressController.open(parent=parent, total_count=total, title="Processing rows…")

    results: list[dict[str, Any]] = []
    try:
        for idx, row in enumerate(rows, start=1):
            try:
                messages = []
                if task.system:
                    messages.append({"role": "system", "content": render_prompt(task, row, text=task.system)})
                messages.append({"role": "user", "content": render_prompt(task, row)})

                resp = client.responses.parse(input=messages, text_format=output_model, **request_params)
                parsed = resp.output_parsed.model_dump()

                combined = {col: row.get(col) for col in task.carry_columns}
                combined.update(parsed)
                results.append(combined)
            except ValidationError as ve:
                print(f"[VALIDATION ERROR] row {idx} -> {ve}")
            except Exception as e:
                print(f"[API ERROR] row {idx} -> {e}")
            finally:
                progress.update(idx, message=f"Processed {idx} of {total} rows")
    finally:
        progress.close()

    result_df = to_long_df(results)
    save_as_csv(result_df)
