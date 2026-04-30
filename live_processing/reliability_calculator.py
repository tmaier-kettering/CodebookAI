import tkinter as tk
import customtkinter as ctk
import pandas as pd

# Import dialog wrappers
try:
    from ui.dialogs import show_error, show_info, ask_save_filename
except ImportError:
    from tkinter import messagebox, filedialog
    show_error = messagebox.showerror
    show_info = messagebox.showinfo
    ask_save_filename = filedialog.asksaveasfilename

from ui.two_page_wizard import WizardResult, open_two_page_wizard


# ----------------------------- Stats -----------------------------

def compute_cohens_kappa(series_a: pd.Series, series_b: pd.Series) -> float:
    """
    Cohen's kappa for two categorical series (same length).
    Handles mismatched/partial label sets by aligning marginals over the union of labels.
    """
    s1 = series_a.astype(str)
    s2 = series_b.astype(str)
    if len(s1) != len(s2) or len(s1) == 0:
        return float("nan")

    table = pd.crosstab(s1, s2)
    n = table.values.sum()
    if n == 0:
        return float("nan")

    # Observed agreement
    po = table.values.trace() / n

    # Expected agreement by chance: sum_k p_row(k) * p_col(k), over the UNION of labels
    row_marg = (table.sum(axis=1) / n)  # index = labels from coder A
    col_marg = (table.sum(axis=0) / n)  # index = labels from coder B

    # Align to the union of labels so shapes match
    labels_union = row_marg.index.union(col_marg.index)
    p_row = row_marg.reindex(labels_union, fill_value=0.0)
    p_col = col_marg.reindex(labels_union, fill_value=0.0)

    pe = float((p_row * p_col).sum())

    # Guard against division by zero when pe == 1
    if pe >= 1.0:
        return 1.0
    return float((po - pe) / (1.0 - pe))



# ----------------------------- Finish Handler -----------------------------

def reliability_finish_handler(res: WizardResult, win: tk.Toplevel) -> bool:
    """
    Default reliability behavior:
      - inner-join on text (already done in res.merged)
      - add 'agreement' column
      - compute % agreement and Cohen's kappa
      - prompt for Excel save and write two sheets
    Returns True to close the wizard.
    """
    merged = res.merged.copy()
    merged["agreement"] = merged[res.ds1_name] == merged[res.ds2_name]

    num_rows = int(len(merged))
    percent_agree = float(merged["agreement"].mean() * 100.0) if num_rows > 0 else float("nan")
    kappa = compute_cohens_kappa(merged[res.ds1_name], merged[res.ds2_name]) if num_rows > 0 else float("nan")

    default_file = f"agreement_{res.ds1_name}_vs_{res.ds2_name}.xlsx"
    save_path = ask_save_filename(
        title="Save results (Excel)",
        defaultextension=".xlsx",
        filetypes=[("Excel Workbook", "*.xlsx"), ("All files", "*.*")],
        initialfile=default_file,
        parent=win
    )
    if not save_path:
        # still okay—close and return the in-memory result only
        win.result = {
            "dataframe": merged,
            "percent_agreement": percent_agree,
            "kappa": kappa,
            "saved_path": None,
            "dataset1_name": res.ds1_name,
            "dataset2_name": res.ds2_name,
        }
        return True

    try:
        stats_rows = [
            ("Dataset 1 Name", res.ds1_name or ""),
            ("Dataset 2 Name", res.ds2_name or ""),
            ("Number of Rows (after join on text)", num_rows),
            ("Percent Agreement", percent_agree),
            ("Cohen's Kappa", kappa),
        ]
        stats_df = pd.DataFrame(stats_rows, columns=["Metric", "Value"])
        data_df = merged[["text", res.ds1_name, res.ds2_name, "agreement"]].copy()

        # Write Excel
        with pd.ExcelWriter(save_path, engine="openpyxl") as writer:
            stats_df.to_excel(writer, sheet_name="Reliability Statistics", index=False)
            data_df.to_excel(writer, sheet_name="Data", index=False)

        win.result = {
            "dataframe": merged,
            "percent_agreement": percent_agree,
            "kappa": kappa,
            "saved_path": save_path,
            "dataset1_name": res.ds1_name,
            "dataset2_name": res.ds2_name,
        }
        return True

    except Exception as e:
        show_error("Save Error", f"Failed to save Excel file:\n{e}", parent=win)
        return False  # keep wizard open so the user can try again


# ----------------------------- Public Entry -----------------------------

def open_reliability_wizard(parent: tk.Misc):
    """
    Opens the reusable two-page wizard and runs the reliability handler on finish.
    Returns a dict with:
      - dataframe (merged with 'text', ds1_name, ds2_name, 'agreement')
      - percent_agreement
      - kappa
      - saved_path
      - dataset1_name
      - dataset2_name
    or None if cancelled.
    """
    return open_two_page_wizard(parent, on_finish=reliability_finish_handler)


