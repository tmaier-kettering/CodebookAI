# csv_handling.py

from __future__ import annotations

import csv
import io
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox


# -----------------------------
# Internal Tk convenience utils
# -----------------------------

def _ensure_parent(parent: Optional[tk.Misc]) -> Tuple[tk.Misc, Optional[tk.Tk]]:
    """
    Ensure we have a Tk parent to own dialogs and Tk variables.

    If `parent` is provided, we use it and create no new root.
    If `parent` is None, we create a *hidden* root, return it, and also return
    the created root so the caller can optionally destroy it later.

    Returns:
        (owner, created_root)
        owner: a tk.Misc you can safely use as the 'master'/'parent'
        created_root: the hidden root we created (or None if not created)
    """
    if parent is not None:
        return parent, None

    created_root = tk.Tk()
    # Keep it completely hidden but fully initialized so dialogs don't hang
    created_root.withdraw()
    try:
        created_root.attributes("-topmost", True)
    except Exception:
        pass
    created_root.update_idletasks()
    return created_root, created_root


def _safe_destroy(maybe_root: Optional[tk.Tk]) -> None:
    """Destroy a created hidden root (no-op if None)."""
    if maybe_root is not None:
        try:
            maybe_root.destroy()
        except Exception:
            pass


# ---------------------------------------
# Public API: CSV import (UI-driven)
# ---------------------------------------

def import_csv(parent: Optional[tk.Misc] = None,
               title: str = "Import CSV",
               filetypes: Sequence[Tuple[str, str]] = (("CSV files", "*.csv"), ("All files", "*.*"))
               ) -> Optional[List[str]]:
    """
    Show a small modal dialog to browse for a CSV and choose whether to skip the first row.
    Returns a list of labels taken from the FIRST column, or None if cancelled.

    IMPORTANT:
      - No additional `Tk()` root or `mainloop()` is created.
      - If you have an existing Tk app, pass its root or any widget as `parent`.
      - If `parent` is None, a temporary hidden root is created and cleaned up.

    Args:
        parent: A tk widget (e.g., your main window) to own the dialog. Optional.
        title:  Window title.
        filetypes: Tuple of (description, pattern) for file dialog filtering.

    Returns:
        list[str] | None
    """
    owner, created_root = _ensure_parent(parent)

    # Modal Toplevel dialog
    dlg = tk.Toplevel(owner)
    dlg.title(title)
    dlg.transient(owner)
    dlg.grab_set()  # modal
    dlg.resizable(False, False)

    # Widgets
    tk.Label(dlg, text="CSV File:").grid(row=0, column=0, padx=8, pady=(10, 4), sticky="e")
    file_entry = tk.Entry(dlg, width=52)
    file_entry.grid(row=0, column=1, padx=4, pady=(10, 4), sticky="w")

    def browse_file():
        path = filedialog.askopenfilename(parent=dlg, title=title, filetypes=list(filetypes))
        if path:
            file_entry.delete(0, tk.END)
            file_entry.insert(0, path)

    tk.Button(dlg, text="Browse…", command=browse_file).grid(row=0, column=2, padx=8, pady=(10, 4))

    has_headers = tk.BooleanVar(master=dlg, value=False)  # bind var to this dialog!
    tk.Checkbutton(dlg, text="CSV has headers (skip first row)", variable=has_headers)\
        .grid(row=1, column=1, padx=4, pady=4, sticky="w")

    # Store result in closure
    result: dict[str, Optional[List[str]]] = {"labels": None}

    def process_and_close():
        path = file_entry.get().strip()
        if not path:
            messagebox.showerror("Error", "No file selected.", parent=dlg)
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                rows = list(csv.reader(f))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{e}", parent=dlg)
            return

        if not rows:
            messagebox.showerror("Error", "The file is empty.", parent=dlg)
            return

        rows_to_use = rows[1:] if has_headers.get() else rows

        if any(len(r) > 1 for r in rows_to_use):
            cont = messagebox.askokcancel(
                "Warning",
                "The CSV appears to have more than one column.\n"
                "Only the FIRST column will be used.\n\nContinue?",
                parent=dlg
            )
            if not cont:
                return

        labels = [r[0] for r in rows_to_use if r]
        result["labels"] = labels
        dlg.destroy()

    # Buttons
    btns = tk.Frame(dlg)
    btns.grid(row=2, column=0, columnspan=3, sticky="e", padx=8, pady=(8, 10))
    tk.Button(btns, text="Cancel", command=dlg.destroy).grid(row=0, column=0, padx=4)
    tk.Button(btns, text="Process", command=process_and_close).grid(row=0, column=1, padx=4)

    # Default focus behavior
    file_entry.focus_set()

    # Position the dialog relative to owner
    dlg.update_idletasks()
    try:
        x = owner.winfo_rootx() + 60
        y = owner.winfo_rooty() + 60
    except Exception:
        # Owner might be a withdrawn temp root
        x = y = 100
    dlg.geometry(f"+{x}+{y}")

    # Block until dialog is closed (no extra mainloop)
    owner.wait_window(dlg)

    # Clean up temp root if we created one
    _safe_destroy(created_root)

    return result["labels"]


# -------------------------------------------------------
# Public API: Save CSV from structured classifications
# -------------------------------------------------------

def save_classifications_to_csv(data: List[Dict[str, Any]],
                                parent: Optional[tk.Misc] = None,
                                default_name: str = "classifications.csv"
                                ) -> Optional[str]:
    """
    Save a CSV with headers 'text,label,confidence' from the NEW structure:

        [
          { "classifications": [
              {"quote": "...", "label": "...", "confidence": 0.9},
              ...
            ]
          },
          ...
        ]

    Returns the saved file path, or None if the user cancels.
    Does not create a second mainloop; owns dialogs correctly.
    """
    # Validate input early
    if not isinstance(data, list):
        raise ValueError("Expected a list of dicts for 'data' (new structure).")

    # Build rows
    rows: List[Tuple[str, str, str]] = []
    for i, obj in enumerate(data):
        if not isinstance(obj, dict):
            raise ValueError(f"data[{i}] must be a dict.")
        cl = obj.get("classifications")
        if not isinstance(cl, list):
            raise ValueError(f"data[{i}]['classifications'] must be a list.")
        for j, item in enumerate(cl):
            if not isinstance(item, dict):
                raise ValueError(f"data[{i}]['classifications'][{j}] must be a dict.")
            text = str(item.get("quote", "") or "")
            label = str(item.get("label", "") or "")
            conf = item.get("confidence", "")
            conf_str = f"{conf:.6f}" if isinstance(conf, float) else (str(conf) if conf is not None else "")
            rows.append((text, label, conf_str))

    # Ask where to save
    owner, created_root = _ensure_parent(parent)
    try:
        path = filedialog.asksaveasfilename(
            parent=owner,
            title="Save classifications as CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_name,
        )
    finally:
        _safe_destroy(created_root)

    if not path:
        return None

    # Write CSV
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["text", "label", "confidence"])
        if rows:
            w.writerows(rows)

    return path


# -------------------------------------------------------------------
# Public API: Parse batch JSONL bytes and prompt to save as CSV file
# -------------------------------------------------------------------

def save_classifications_csv_from_content_bytes(content_bytes: bytes,
                                                parent: Optional[tk.Misc] = None,
                                                default_name: str = "batch_classifications.csv"
                                                ) -> Optional[str]:
    """
    Parse OpenAI batch JSONL bytes and prompt the user to save a CSV locally.
    CSV headers: text,label,confidence

    - Robust to headless contexts (falls back to Desktop / CWD if Tk dialogs fail).
    - No extra mainloop; dialogs are owned by your `parent` (or a hidden root).
    """
    # ---- Parse JSONL into rows ----
    jsonl_text = content_bytes.decode("utf-8", errors="replace")
    rows: List[Tuple[str, str, str]] = []

    for raw_line in jsonl_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        body = obj.get("response", {}).get("body", {})
        outputs = body.get("output", []) or []
        msg = next((o for o in outputs if o.get("type") == "message"), None)
        if not msg:
            continue

        content_list = msg.get("content", []) or []
        text_chunk = next((c for c in content_list if c.get("type") == "output_text" and "text" in c), None)
        if not text_chunk:
            continue

        try:
            payload = json.loads(text_chunk["text"])
        except json.JSONDecodeError:
            continue

        for c in payload.get("classifications", []):
            quote = str(c.get("quote", "") or "")
            label = str(c.get("label", "") or "")
            conf = c.get("confidence", "")
            conf_str = f"{conf:.6f}" if isinstance(conf, float) else (str(conf) if conf is not None else "")
            rows.append((quote, label, conf_str))

    # Compose CSV in-memory
    buf = io.StringIO(newline="")
    w = csv.writer(buf)
    w.writerow(["text", "label", "confidence"])
    if rows:
        w.writerows(rows)
    csv_bytes = buf.getvalue().encode("utf-8")

    # ---- AskWhereToSave with robust fallbacks ----
    try:
        owner, created_root = _ensure_parent(parent)
        try:
            path = filedialog.asksaveasfilename(
                parent=owner,
                title="Save classifications CSV",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=default_name,
            )
        finally:
            _safe_destroy(created_root)
    except Exception:
        # Headless, or Tk problems – save to Desktop/CWD with timestamp
        base, ext = os.path.splitext(default_name)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fallback = f"{base}_{stamp}{ext}"

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        path = os.path.join(desktop, fallback) if os.path.isdir(desktop) else os.path.abspath(fallback)

    if not path:
        # User cancelled
        return None

    with open(path, "wb") as f:
        f.write(csv_bytes)

    return path
