from collections.abc import Sequence, Iterable
from enum import Enum
import customtkinter as ctk

# Import dialog wrappers
try:
    from ui.dialogs import show_info, ask_save_filename
except ImportError:
    from tkinter import messagebox, filedialog
    show_info = messagebox.showinfo
    ask_save_filename = filedialog.asksaveasfilename

import pandas as pd


def make_str_enum(name: str, values: list[str]) -> type[Enum]:
    """
    Create a string-valued Enum dynamically so we can plug the user's label list
    directly into the schema enforced by Structured Outputs.
    """
    return Enum(name, {v: v for v in values}, type=str)


def save_as_csv(df: "pd.DataFrame"):
    # Prompt user to save results
    file_path = ask_save_filename(
        title="Save classifications as CSV",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialfile="classifications.csv",
    )

    if file_path:  # Only save if user didn't cancel
        df.to_csv(file_path, index=False)
        show_info("Success", f"Classifications saved to {file_path}")
    else:
        show_info("Cancelled", "Save operation cancelled.")


def to_long_df(records):
    """
    records: iterable of objects with .model_dump() -> dict
    - Builds a DataFrame from whatever keys exist.
    - Flattens nested dicts.
    - Explodes ALL list-like columns (lists/tuples/sets).
    """
    # 1) Collect dicts (model_dump) and flatten nested dicts
    try:
        raw = [r.model_dump() for r in records]
    except Exception:
        raw = records # assume already dicts
    df = pd.json_normalize(raw, sep='.')  # flattens nested dicts into columns like 'meta.author'

    # 2) Detect list-like columns (skip strings/bytes)
    def is_listy(x):
        return isinstance(x, Sequence) and not isinstance(x, (str, bytes))

    list_cols = [
        c for c in df.columns
        if df[c].apply(is_listy).any()
    ]

    # 3) Explode all list-like columns (handles 0, 1, or many)
    if list_cols:
        df = df.explode(list_cols, ignore_index=True)

    # 4) (Optional) drop rows where any exploded col is NA
    if list_cols:
        df = df.dropna(subset=list_cols, how='any')

    return df


def join_datasets(datasets):
    if datasets is None:
        return ""
    if isinstance(datasets, (str, bytes)):
        return datasets
    if isinstance(datasets, Iterable):
        return ",".join(map(str, datasets))
    return str(datasets)