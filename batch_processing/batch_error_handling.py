import json
import customtkinter as ctk
import pandas as pd

# Import dialog wrappers
try:
    from ui.dialogs import show_error, ask_save_filename
except ImportError:
    from tkinter import messagebox, filedialog
    show_error = messagebox.showerror
    ask_save_filename = filedialog.asksaveasfilename


def handle_batch_fail(client, status):
    show_error("Batch Failed",
                         "The batch job failed. You will be given the option to save a basic error readout as a CSV and the fill error JSONL file.")

    file_response = client.files.content(status.error_file_id)

    output = []
    for line in file_response.text.splitlines():
        individual_batch = json.loads(line)
        output.append(individual_batch['response']['body']['error'])

    output = pd.DataFrame(output)

    # Prompt user to save the results
    file_path = ask_save_filename(
        title="Save errors to CSV",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialfile="errors.csv",
    )

    if file_path:  # Only save if user didn't cancel
        output.to_csv(file_path, index=False)

    # Prompt user to save the results
    file_path = ask_save_filename(
        title="Save full error jsonl",
        defaultextension=".jsonl",
        filetypes=[("JSONL files", "*.jsonl"), ("All files", "*.*")],
        initialfile="errors.jsonl",
    )

    if file_path:  # Only save if user didn't cancel
        file_response.write_to_file(file_path)