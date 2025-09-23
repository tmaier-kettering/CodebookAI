"""
Inter-Rater Reliability Calculator

This module provides a multi-page GUI wizard for calculating inter-rater reliability
between two datasets. It allows users to select text and label columns from two
different datasets, merges them based on shared text, and calculates percent agreement
and Cohen's kappa.

Features:
- 4-page wizard interface
- File selection for CSV, Excel, TSV, and other tabular formats
- Preview table with header checkbox support
- Column selection via radio buttons
- Data validation (matching lengths)
- Shared text extraction
- Agreement calculation
- Cohen's kappa calculation
- Results display and dataset export

Author: Generated for CodebookAI
"""

from __future__ import annotations

import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from typing import Optional, List, Dict, Sequence, Tuple
import pandas as pd


def calculate_interrater_reliability(parent: Optional[tk.Misc] = None) -> None:
    """
    Main function to open the Inter-Rater Reliability Calculator GUI.
    
    Args:
        parent: Parent tkinter widget. If None, creates a new root window.
    """
    # Ensure parent window
    owner, created_root = _ensure_parent(parent)
    
    try:
        # Create and run the wizard
        wizard = IRRWizard(owner)
        wizard.run()
    finally:
        # Clean up created root if needed
        _safe_destroy(created_root)


class IRRWizard:
    """Multi-page wizard for Inter-Rater Reliability calculation."""
    
    def __init__(self, parent: tk.Misc):
        self.parent = parent
        self.current_page = 0
        self.total_pages = 4
        
        # Data storage for each page
        self.page_data = [
            {"title": "Dataset 1 - Text Column", "data": None, "selected_column": None},
            {"title": "Dataset 1 - Labels Column", "data": None, "selected_column": None},
            {"title": "Dataset 2 - Text Column", "data": None, "selected_column": None},
            {"title": "Dataset 2 - Labels Column", "data": None, "selected_column": None},
        ]
        
        self.dialog = None
        
    def run(self):
        """Run the wizard dialog."""
        self._create_dialog()
        self._show_current_page()
        
        # Block until dialog is closed
        self.parent.wait_window(self.dialog)
        
    def _create_dialog(self):
        """Create the main dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Inter-Rater Reliability Calculator")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(True, True)
        
        # Configure grid weights for responsive layout
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(1, weight=1)  # Content area grows
        
        # Header with progress indicator
        self._create_header()
        
        # Main content frame
        self.content_frame = ttk.Frame(self.dialog)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        
        # Footer with navigation buttons
        self._create_footer()
        
        # Set initial geometry
        self.dialog.geometry("800x600")
        
    def _create_header(self):
        """Create the header with title and progress indicator."""
        header_frame = ttk.Frame(self.dialog)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        header_frame.columnconfigure(1, weight=1)
        
        # Progress indicator
        progress_text = f"Step {self.current_page + 1} of {self.total_pages}"
        self.progress_label = ttk.Label(header_frame, text=progress_text)
        self.progress_label.grid(row=0, column=0, sticky="w")
        
        # Page title
        self.title_label = ttk.Label(header_frame, text="", font=("Segoe UI", 14, "bold"))
        self.title_label.grid(row=0, column=1, pady=(0, 10))
        
    def _create_footer(self):
        """Create the footer with navigation buttons."""
        footer_frame = ttk.Frame(self.dialog)
        footer_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        footer_frame.columnconfigure(1, weight=1)
        
        # Previous button
        self.prev_button = ttk.Button(footer_frame, text="← Previous", command=self._prev_page)
        self.prev_button.grid(row=0, column=0, sticky="w")
        
        # Cancel button (center)
        self.cancel_button = ttk.Button(footer_frame, text="Cancel", command=self._cancel)
        self.cancel_button.grid(row=0, column=1)
        
        # Next/Finish button
        self.next_button = ttk.Button(footer_frame, text="Next →", command=self._next_page)
        self.next_button.grid(row=0, column=2, sticky="e")
        
    def _show_current_page(self):
        """Display the current page content."""
        # Update header
        progress_text = f"Step {self.current_page + 1} of {self.total_pages}"
        self.progress_label.config(text=progress_text)
        self.title_label.config(text=self.page_data[self.current_page]["title"])
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Create page content
        if self.current_page < 4:
            self._create_data_selection_page()
        
        # Update button states
        self._update_button_states()
        
    def _create_data_selection_page(self):
        """Create a data selection page (file, preview, column selection)."""
        page_frame = ttk.Frame(self.content_frame)
        page_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        page_frame.columnconfigure(0, weight=1)
        page_frame.rowconfigure(3, weight=1)  # Preview area grows
        
        # Instruction
        instruction_text = self._get_page_instruction()
        instr_label = ttk.Label(page_frame, text=instruction_text, wraplength=700)
        instr_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        # File selection
        file_frame = ttk.Frame(page_frame)
        file_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="File:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_var, state="readonly")
        self.file_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        
        browse_btn = ttk.Button(file_frame, text="Browse...", command=self._browse_file)
        browse_btn.grid(row=0, column=2)
        
        # Header checkbox
        self.has_headers_var = tk.BooleanVar(master=self.dialog, value=True)
        header_chk = ttk.Checkbutton(
            page_frame, 
            text="File has headers (skip first row)", 
            variable=self.has_headers_var, 
            command=self._refresh_preview
        )
        header_chk.grid(row=2, column=0, sticky="w", pady=(0, 10))
        
        # Preview area
        preview_frame = ttk.LabelFrame(page_frame, text="Preview (first 5 rows)")
        preview_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(1, weight=1)
        
        # Column selection (radio buttons)
        self.column_frame = ttk.Frame(preview_frame)
        self.column_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Preview table
        table_frame = ttk.Frame(preview_frame)  
        table_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        self.preview_tree = ttk.Treeview(table_frame)
        self.preview_tree.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbars for preview
        h_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.preview_tree.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.preview_tree.configure(xscrollcommand=h_scroll.set)
        
        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.preview_tree.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        self.preview_tree.configure(yscrollcommand=v_scroll.set)
        
        # Initialize variables for this page
        self.selected_column_var = tk.IntVar()
        self.current_data = None
        self.column_radios = []
        
    def _get_page_instruction(self) -> str:
        """Get instruction text for current page."""
        instructions = [
            "Select the file containing the text data for Dataset 1. Choose exactly one column that contains the text to be compared.",
            "Select the file containing the label data for Dataset 1. Choose exactly one column that contains the labels. This must have the same number of rows as the text data.",
            "Select the file containing the text data for Dataset 2. Choose exactly one column that contains the text to be compared.",
            "Select the file containing the label data for Dataset 2. Choose exactly one column that contains the labels. This must have the same number of rows as the text data."
        ]
        return instructions[self.current_page]
        
    def _browse_file(self):
        """Open file browser to select a data file."""
        filetypes = [
            ("All supported", "*.csv *.xlsx *.xls *.tsv *.txt"),
            ("CSV files", "*.csv"),
            ("Excel files", "*.xlsx *.xls"),
            ("TSV files", "*.tsv"),
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            parent=self.dialog,
            title="Select data file",
            filetypes=filetypes
        )
        
        if filename:
            self.file_var.set(filename)
            self._load_file_data(filename)
            self._refresh_preview()
            
    def _load_file_data(self, filepath: str):
        """Load data from selected file."""
        try:
            # Determine file type and load data
            path = Path(filepath)
            suffix = path.suffix.lower()
            
            if suffix in ['.xlsx', '.xls']:
                # Excel file
                df = pd.read_excel(filepath, header=None)
                self.current_data = df.values.tolist()
            else:
                # Assume CSV/TSV/TXT
                # Try to detect delimiter
                with open(filepath, 'r', encoding='utf-8') as f:
                    sample = f.read(1024)
                    
                delimiter = ','  # default
                if '\t' in sample and sample.count('\t') > sample.count(','):
                    delimiter = '\t'
                    
                # Load with detected delimiter
                with open(filepath, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.reader(f, delimiter=delimiter)
                    self.current_data = list(reader)
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
            self.current_data = None
            
    def _refresh_preview(self):
        """Refresh the preview table and column selection."""
        if not self.current_data:
            return
            
        # Clear existing preview
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
            
        # Clear column radio buttons
        for radio in self.column_radios:
            radio.destroy()
        self.column_radios.clear()
        
        if not self.current_data:
            return
            
        # Determine if we should skip headers
        skip_header = self.has_headers_var.get()
        data_start = 1 if skip_header else 0
        
        # Set up treeview columns
        if len(self.current_data) > 0:
            num_cols = len(self.current_data[0])
            cols = [f"col_{i}" for i in range(num_cols)]
            
            self.preview_tree["columns"] = cols
            self.preview_tree["show"] = "tree headings"
            
            # Configure column headers and radio buttons
            for i, col_id in enumerate(cols):
                if skip_header and len(self.current_data) > 0:
                    header_text = str(self.current_data[0][i]) if i < len(self.current_data[0]) else f"Column {i+1}"
                else:
                    header_text = f"Column {i+1}"
                    
                self.preview_tree.heading(col_id, text=header_text)
                self.preview_tree.column(col_id, width=100, minwidth=50)
                
                # Create radio button for column selection
                radio = ttk.Radiobutton(
                    self.column_frame,
                    text=header_text,
                    variable=self.selected_column_var,
                    value=i
                )
                radio.grid(row=0, column=i, padx=5, sticky="w")
                self.column_radios.append(radio)
                
            # Add preview data (first 5 rows after header if applicable)
            preview_data = self.current_data[data_start:data_start + 5]
            for row_data in preview_data:
                # Pad row if needed
                padded_row = row_data + [''] * (num_cols - len(row_data))
                self.preview_tree.insert("", "end", values=padded_row[:num_cols])
                
    def _update_button_states(self):
        """Update the state of navigation buttons."""
        # Previous button
        self.prev_button.config(state="normal" if self.current_page > 0 else "disabled")
        
        # Next/Finish button
        if self.current_page == self.total_pages - 1:
            self.next_button.config(text="Calculate", command=self._finish)
        else:
            self.next_button.config(text="Next →", command=self._next_page)
            
    def _prev_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._show_current_page()
            
    def _next_page(self):
        """Go to next page or finish."""
        if self._validate_current_page():
            self._save_current_page_data()
            if self.current_page < self.total_pages - 1:
                self.current_page += 1
                self._show_current_page()
                
    def _validate_current_page(self) -> bool:
        """Validate current page data before proceeding."""
        if not hasattr(self, 'current_data') or not self.current_data:
            messagebox.showerror("Error", "Please select a file first.")
            return False
            
        # Check if a column is selected
        if not hasattr(self, 'selected_column_var'):
            messagebox.showerror("Error", "Please select a column.")
            return False
            
        return True
        
    def _save_current_page_data(self):
        """Save current page data for later processing."""
        if not hasattr(self, 'current_data') or not self.current_data:
            return
            
        skip_header = self.has_headers_var.get()
        data_start = 1 if skip_header else 0
        selected_col = self.selected_column_var.get()
        
        # Extract selected column data
        column_data = []
        for row in self.current_data[data_start:]:
            if selected_col < len(row):
                column_data.append(str(row[selected_col]).strip())
            else:
                column_data.append("")
                
        self.page_data[self.current_page]["data"] = column_data
        self.page_data[self.current_page]["selected_column"] = selected_col
        
    def _finish(self):
        """Finish wizard and calculate inter-rater reliability."""
        if not self._validate_current_page():
            return
            
        self._save_current_page_data()
        
        # Validate all data is collected
        for i, page in enumerate(self.page_data):
            if not page["data"]:
                messagebox.showerror("Error", f"Missing data for {page['title']}")
                return
                
        # Validate matching lengths within each dataset
        dataset1_text = self.page_data[0]["data"]
        dataset1_labels = self.page_data[1]["data"]
        dataset2_text = self.page_data[2]["data"]
        dataset2_labels = self.page_data[3]["data"]
        
        if len(dataset1_text) != len(dataset1_labels):
            messagebox.showerror("Error", 
                               f"Dataset 1 text ({len(dataset1_text)} rows) and labels ({len(dataset1_labels)} rows) must have the same length.")
            return
            
        if len(dataset2_text) != len(dataset2_labels):
            messagebox.showerror("Error", 
                               f"Dataset 2 text ({len(dataset2_text)} rows) and labels ({len(dataset2_labels)} rows) must have the same length.")
            return
            
        # Process data and calculate reliability
        self._process_and_calculate()
        
    def _process_and_calculate(self):
        """Process the data and calculate inter-rater reliability."""
        try:
            # Get data
            dataset1_text = self.page_data[0]["data"]
            dataset1_labels = self.page_data[1]["data"]
            dataset2_text = self.page_data[2]["data"] 
            dataset2_labels = self.page_data[3]["data"]
            
            # Create DataFrames for easier processing
            df1 = pd.DataFrame({'text': dataset1_text, 'label1': dataset1_labels})
            df2 = pd.DataFrame({'text': dataset2_text, 'label2': dataset2_labels})
            
            # Find shared text (inner join)
            merged_df = pd.merge(df1, df2, on='text', how='inner')
            
            if len(merged_df) == 0:
                messagebox.showerror("Error", "No shared text found between the two datasets.")
                return
                
            # Add agreement column
            merged_df['agreement'] = merged_df['label1'] == merged_df['label2']
            
            # Calculate metrics
            total_cases = len(merged_df)
            agreements = merged_df['agreement'].sum()
            percent_agreement = (agreements / total_cases) * 100 if total_cases > 0 else 0
            
            # Calculate Cohen's kappa
            kappa = self._calculate_cohens_kappa(merged_df['label1'].tolist(), merged_df['label2'].tolist())
            
            # Show results
            result_message = (
                f"Inter-Rater Reliability Results:\n\n"
                f"Total shared text entries: {total_cases}\n"
                f"Agreements: {agreements}\n"
                f"Percent Agreement: {percent_agreement:.2f}%\n"
                f"Cohen's Kappa: {kappa:.4f}\n\n"
                f"Kappa Interpretation:\n"
                f"• < 0.20: Poor agreement\n"
                f"• 0.21-0.40: Fair agreement\n" 
                f"• 0.41-0.60: Moderate agreement\n"
                f"• 0.61-0.80: Good agreement\n"
                f"• 0.81-1.00: Very good agreement"
            )
            
            messagebox.showinfo("Results", result_message)
            
            # Offer to save dataset
            self._save_dataset(merged_df)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate reliability: {str(e)}")
            
    def _calculate_cohens_kappa(self, rater1: List[str], rater2: List[str]) -> float:
        """Calculate Cohen's kappa coefficient manually."""
        if len(rater1) != len(rater2):
            raise ValueError("Rater arrays must have the same length")
            
        n = len(rater1)
        if n == 0:
            return 0.0
            
        # Get all unique categories
        categories = sorted(set(rater1 + rater2))
        k = len(categories)
        
        if k <= 1:
            return 1.0  # Perfect agreement if only one category
            
        # Create category to index mapping
        cat_to_idx = {cat: i for i, cat in enumerate(categories)}
        
        # Build confusion matrix
        confusion_matrix = [[0] * k for _ in range(k)]
        for r1, r2 in zip(rater1, rater2):
            i, j = cat_to_idx[r1], cat_to_idx[r2]
            confusion_matrix[i][j] += 1
            
        # Calculate observed agreement (Po)
        po = sum(confusion_matrix[i][i] for i in range(k)) / n
        
        # Calculate expected agreement (Pe)
        marginal_1 = [sum(confusion_matrix[i][j] for j in range(k)) / n for i in range(k)]
        marginal_2 = [sum(confusion_matrix[i][j] for i in range(k)) / n for j in range(k)]
        pe = sum(marginal_1[i] * marginal_2[i] for i in range(k))
        
        # Calculate kappa
        if pe == 1.0:
            return 1.0
        return (po - pe) / (1 - pe)
        
    def _save_dataset(self, df: pd.DataFrame):
        """Prompt user to save the merged dataset."""
        save_file = filedialog.asksaveasfilename(
            parent=self.dialog,
            title="Save Inter-Rater Reliability Dataset",
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("All files", "*.*")
            ],
            initialfile="interrater_reliability_data.csv"
        )
        
        if save_file:
            try:
                if save_file.endswith('.xlsx'):
                    df.to_excel(save_file, index=False)
                else:
                    df.to_csv(save_file, index=False)
                messagebox.showinfo("Success", f"Dataset saved to {save_file}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save dataset: {str(e)}")
                
    def _cancel(self):
        """Cancel the wizard."""
        self.dialog.destroy()


# Utility functions (copied from data_import.py)
def _ensure_parent(parent: Optional[tk.Misc]) -> tuple[tk.Misc, Optional[tk.Tk]]:
    """Ensure we have a valid parent widget."""
    if parent is not None:
        return parent, None
    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass
    root.update_idletasks()
    return root, root


def _safe_destroy(maybe_root: Optional[tk.Tk]) -> None:
    """Safely destroy a root window if it exists."""
    if maybe_root is not None:
        try:
            maybe_root.destroy()
        except Exception:
            pass


# For testing
if __name__ == "__main__":
    calculate_interrater_reliability()