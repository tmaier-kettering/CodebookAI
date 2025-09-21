import tkinter as tk
from tkinter import filedialog, messagebox
import csv, io, json
from typing import Any, Dict, List, Optional

def import_csv(title="Import CSV", filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))):
    """
    Import the first column of a CSV file via a GUI file dialog.
    - 'title': Title of the file dialog window.
    - 'filetypes': Tuple specifying the file types for the dialog.
    """

    def browse_file():
        file_path = filedialog.askopenfilename(
            title=title,
            filetypes=[filetypes]
        )
        if file_path:
            file_entry.delete(0, tk.END)
            file_entry.insert(0, file_path)

    def process_file():
        file_path = file_entry.get()
        if not file_path:
            messagebox.showerror("Error", "No file selected.")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                rows = list(reader)

                if not rows:
                    messagebox.showerror("Error", "The file is empty.")
                    return None

                if has_headers_var.get():
                    rows = rows[1:]  # Remove the first row if headers checkbox is checked

                if any(len(row) > 1 for row in rows):
                    proceed = messagebox.askokcancel(
                        "Warning",
                        "The CSV file has more than one column. Only the first column will be used. Do you want to proceed?"
                    )
                    if not proceed:
                        return None

                labels = [row[0] for row in rows if row]  # Extract the first column
                # messagebox.showinfo("Success", f"Processed {len(labels)} rows.")
                return labels
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process the file: {e}")
            return None

    # Create the main window
    root = tk.Tk()
    root.title(title)

    # File input field and browse button
    tk.Label(root, text="CSV File:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    file_entry = tk.Entry(root, width=50)
    file_entry.grid(row=0, column=1, padx=5, pady=5)
    browse_button = tk.Button(root, text="Browse", command=browse_file)
    browse_button.grid(row=0, column=2, padx=5, pady=5)

    # Checkbox for headers
    has_headers_var = tk.BooleanVar()
    headers_checkbox = tk.Checkbutton(root, text="CSV has headers", variable=has_headers_var)
    headers_checkbox.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    # Process button
    process_button = tk.Button(root, text="Process", command=lambda: root.quit())
    process_button.grid(row=2, column=1, padx=5, pady=10)

    root.mainloop()

    # Process the file and return the labels
    labels = process_file()
    root.destroy()
    return labels


def save_classifications_to_csv(data: List[Dict[str, Any]]) -> Optional[str]:
    """
    Write a CSV with headers 'text', 'label', 'confidence' from the NEW structure:

        [
          { "classifications": [ {"quote": "...", "label": "...", "confidence": 0.9}, ... ] },
          { "classifications": [ ... ] },
          ...
        ]

    Returns the saved file path, or None if the user cancels.
    """
    if not isinstance(data, list):
        raise ValueError("Expected a list of dicts for 'data' (new structure).")

    rows: List[List[str]] = []
    for i, obj in enumerate(data):
        if not isinstance(obj, Dict):
            raise ValueError(f"data[{i}] must be a dict.")
        cl = obj.get("classifications")
        if not isinstance(cl, list):
            raise ValueError(f"data[{i}]['classifications'] must be a list.")

        for j, item in enumerate(cl):
            if not isinstance(item, Dict):
                raise ValueError(f"data[{i}]['classifications'][{j}] must be a dict.")

            text = item.get("quote", "")
            label = item.get("label", "")
            confidence = item.get("confidence", "")

            # Ensure confidence is a string for CSV
            if isinstance(confidence, float):
                # Format to a sensible precision; tweak as desired
                confidence = f"{confidence:.6f}"
            else:
                confidence = str(confidence) if confidence is not None else ""

            rows.append([text, label, confidence])

    # Tkinter file dialog (no root window shown)
    root = tk.Tk()
    root.withdraw()
    root.update_idletasks()
    file_path = filedialog.asksaveasfilename(
        title="Save classifications as CSV",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialfile="classifications.csv",
    )
    root.destroy()

    if not file_path:
        return None  # user canceled

    # Write CSV
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "label", "confidence"])
        writer.writerows(rows)

    return file_path


def save_classifications_csv_from_content_bytes(content_bytes: bytes, default_name: str = "batch_classifications.csv") -> None:
    """
    One-shot: parse OpenAI batch JSONL bytes and prompt the user (Windows) to save a CSV locally.
    - Brings the 'Save As' dialog to the front.
    - Falls back to console prompt (or auto-save) if Tk isn't available.
    CSV columns: text,label,confidence
    """
    import io, csv, json, os, sys
    from datetime import datetime

    # ---------- Parse JSONL -> rows ----------
    jsonl_text = content_bytes.decode("utf-8", errors="replace")
    rows = []

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
            quote = c.get("quote", "")
            label = c.get("label", "")
            confidence = c.get("confidence", "")
            rows.append((quote, label, confidence))

    # Write CSV to memory
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(["text", "label", "confidence"])
    if rows:
        writer.writerows(rows)
    csv_bytes = buf.getvalue().encode("utf-8")

    # ---------- Save-As (Windows Tk), with robust fallbacks ----------
    path = ""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        # Force it to the front so it doesn't appear "hung" behind other windows
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        root.update()  # ensure the hidden root is initialized

        path = filedialog.asksaveasfilename(
            parent=root,
            title="Save classifications CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=default_name,
        )

        root.destroy()

    except Exception:
        # Headless / Tk not installed / called from a place Tk can't run
        print("GUI save dialog not available. You can type a path or press Enter to save to Desktop.")
        try:
            user_in = input(f"Save path (e.g., C:\\Users\\You\\Documents\\{default_name}): ").strip()
        except EOFError:
            user_in = ""

        if user_in:
            path = user_in
        else:
            # Default to Desktop (Windows) or CWD if Desktop unknown
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if os.path.isdir(desktop):
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = os.path.join(desktop, f"{os.path.splitext(default_name)[0]}_{stamp}.csv")
            else:
                path = os.path.abspath(default_name)

    if path:
        with open(path, "wb") as f:
            f.write(csv_bytes)
        print(f"Saved classifications CSV to: {path}")
    else:
        print("Save cancelled (CSV not written).")
