import json
from tkinter import messagebox, filedialog
import pandas as pd


def handle_batch_fail(client, status):
    messagebox.showerror("Batch Failed",
                         "The batch job failed. You will be given the option to save a basic error readout as a CSV and the fill error JSONL file.")

    file_response = client.files.content(status.error_file_id)

    output = []
    for line in file_response.text.splitlines():
        individual_batch = json.loads(line)
        output.append(individual_batch['response']['body']['error'])

    output = pd.DataFrame(output)

    # Prompt user to save the results
    file_path = filedialog.asksaveasfilename(
        title="Save errors to CSV",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialfile="errors.csv",
    )

    if file_path:  # Only save if user didn't cancel
        output.to_csv(file_path, index=False)

    # Prompt user to save the results
    file_path = filedialog.asksaveasfilename(
        title="Save full error jsonl",
        defaultextension=".jsonl",
        filetypes=[("JSONL files", "*.jsonl"), ("All files", "*.*")],
        initialfile="errors.csv",
    )

    if file_path:  # Only save if user didn't cancel
        file_response.write_to_file(file_path)