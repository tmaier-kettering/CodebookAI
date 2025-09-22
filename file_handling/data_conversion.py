from enum import Enum
from tkinter import filedialog, messagebox

import pandas as pd


def make_str_enum(name: str, values: list[str]) -> type[Enum]:
    """
    Create a string-valued Enum dynamically so we can plug the user's label list
    directly into the schema enforced by Structured Outputs.
    """
    return Enum(name, {v: v for v in values}, type=str)


def save_as_csv(df: "pd.DataFrame"):
    # Prompt user to save results
    file_path = filedialog.asksaveasfilename(
        title="Save classifications as CSV",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialfile="classifications.csv",
    )

    if file_path:  # Only save if user didn't cancel
        df.to_csv(file_path, index=False)
        messagebox.showinfo("Success", f"Classifications saved to {file_path}")
    else:
        messagebox.showinfo("Cancelled", "Save operation cancelled.")

