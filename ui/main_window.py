"""
Main window GUI for CodebookAI text classification application.

This module provides the primary user interface for the CodebookAI application,
including batch job management, live processing controls, and settings access.
The interface displays ongoing and completed batch jobs in tabbed tables.

Updated per request:
- Removed add_btn, tools_btn, and settings_btn (refresh button retained).
- Added a top menu bar with the following structure:
  File > Settings, Exit
  Data Prep > Sample
  LLM Tools > Live Methods > Single Label Text Classification, Multi-Label Text Classification, Text Extraction
            > Batch Methods > Single Label Text Classification
  Data Analysis > Reliability Statistics
  Help > Github Repo
- Added a "Batches" title above the table area at the bottom of the page.
"""

import sys, os
import tkinter as tk
from pathlib import Path
from tkinter import ttk
import webbrowser

from live_processing.correlogram import open_correlogram_wizard
from live_processing.reliability_calculator import open_reliability_wizard
from live_processing.sampler import sample_data

# Handle imports based on how the script is run
try:
    from settings_window import SettingsWindow
    from tooltip import ToolTip
    from ui_utils import center_window
    from ui_helpers import make_tab_with_tree, popup_menu, popup_menu_below_widget
    from batch_operations import (
        call_batch_async,
        refresh_batches_async,
        call_batch_download_async,
        cancel_batch_async,
    )
except ImportError:  # fallback when running as a package (ui.*)
    from ui.settings_window import SettingsWindow
    from ui.tooltip import ToolTip
    from ui.ui_utils import center_window
    from ui.ui_helpers import make_tab_with_tree, popup_menu, popup_menu_below_widget
    from ui.batch_operations import (
        call_batch_async,
        refresh_batches_async,
        call_batch_download_async,
        cancel_batch_async,
    )

# Ensure live modules can be imported when run directly
try:
    import live_processing.multi_label_live
    import live_processing.single_label_live
    import live_processing.keyword_extraction_live
except ImportError:
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import live_processing.multi_label_live
    import live_processing.single_label_live
    import live_processing.keyword_extraction_live

APP_TITLE = "CodebookAI"
APP_SUBTITLE = "A qualitative research tool based on OpenAI's Playground API."
WINDOW_SIZE = (1000, 620)  # width, height


def _open_help_docs():
    webbrowser.open("https://github.com/tmaier-kettering/CodebookAI?tab=readme-ov-file#readme")

def _open_report_bug():
    webbrowser.open("https://github.com/tmaier-kettering/CodebookAI/issues/new")

def asset_path(*parts) -> str:
    # When frozen by PyInstaller, data are unpacked under sys._MEIPASS
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base.joinpath("assets", *parts))


def build_ui(root: tk.Tk) -> None:
    """
    Build and configure the main application user interface.

    This function creates the complete UI layout including:
    - Header with app title & subtitle
    - Top menubar for navigation and actions
    - Tabbed interface for ongoing and completed batch jobs
    - Refresh control and context menus for batch operations

    Args:
        root: The main Tkinter window to build the UI in
    """
    root.title(APP_TITLE)

    # ===== Top-level grid: header, spacer, table area =====
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=0)  # header
    root.rowconfigure(1, weight=1)  # spacer/filler (kept for compatibility)
    root.rowconfigure(2, weight=0)  # table area

    # ===== Header (title & subtitle only; no buttons) =====
    # ===== Header (banner image) =====
    header = ttk.Frame(root, padding=(0, 0))
    header.grid(row=0, column=0, sticky="ew")
    header.columnconfigure(0, weight=1)

    # Load and keep a reference to avoid garbage collection
    # (PNG with transparency is fine with tk.PhotoImage)
    banner_img = tk.PhotoImage(file=asset_path("Banner_Narrow_trans.png"))
    scale_factor = 3
    root.banner_img = banner_img.subsample(scale_factor, scale_factor)  # keep a ref on root

    banner_lbl = ttk.Label(header, image=root.banner_img, anchor="center")
    banner_lbl.grid(row=0, column=0, sticky="n", padx=0, pady=0)

    # ===== Menu Bar =====
    menubar = tk.Menu(root)

    # File
    file_menu = tk.Menu(menubar, tearoff=False)
    file_menu.add_command(label="Settings", command=lambda: SettingsWindow(root))
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.destroy)
    menubar.add_cascade(label="File", menu=file_menu)

    # Data Prep
    data_prep_menu = tk.Menu(menubar, tearoff=False)
    data_prep_menu.add_command(label="Sample", command=lambda: sample_data(root))
    menubar.add_cascade(label="Data Prep", menu=data_prep_menu)

    # LLM Tools > Live Methods / Batch Methods
    llm_tools_menu = tk.Menu(menubar, tearoff=False)

    # Live Methods submenu
    live_methods_menu = tk.Menu(llm_tools_menu, tearoff=False)

    def _single_label_live_call():
        live_processing.single_label_live.single_label_pipeline(root)

    def _multi_label_live_call():
        live_processing.multi_label_live.multi_label_pipeline(root)

    def _keyword_extraction_live_call():
        live_processing.keyword_extraction_live.keyword_extraction_pipeline(root)

    live_methods_menu.add_command(
        label="Single Label Text Classification", command=_single_label_live_call
    )
    live_methods_menu.add_command(
        label="Multi-Label Text Classification", command=_multi_label_live_call
    )
    live_methods_menu.add_command(label="Keyword Extraction", command=_keyword_extraction_live_call)

    # Batch Methods submenu
    batch_methods_menu = tk.Menu(llm_tools_menu, tearoff=False)
    batch_methods_menu.add_command(
        label="Single Label Text Classification",
        command=lambda: call_batch_async(root, type="single_label"),
    )
    batch_methods_menu.add_command(
        label="Multi-Label Text Classification",
        command=lambda: call_batch_async(root, type="multi_label"),
    )
    batch_methods_menu.add_command(
        label="Keyword Extraction",
        command=lambda: call_batch_async(root, type="keyword_extraction"),
    )

    llm_tools_menu.add_cascade(label="Live Methods", menu=live_methods_menu)
    llm_tools_menu.add_cascade(label="Batch Methods", menu=batch_methods_menu)
    menubar.add_cascade(label="LLM Tools", menu=llm_tools_menu)

    # Data Analysis
    data_analysis_menu = tk.Menu(menubar, tearoff=False)
    data_analysis_menu.add_command(label="Reliability Statistics", command=lambda: open_reliability_wizard(root))
    data_analysis_menu.add_command(label="Correlogram", command=lambda: open_correlogram_wizard(root))
    menubar.add_cascade(label="Data Analysis", menu=data_analysis_menu)

    # Help
    help_menu = tk.Menu(menubar, tearoff=False)
    help_menu.add_command(label="Help Docs", command=_open_help_docs)
    help_menu.add_command(label="Report a bug", command=_open_report_bug)
    menubar.add_cascade(label="Help", menu=help_menu)

    root.config(menu=menubar)

    # ===== Table area =====
    table_area = ttk.Frame(root, padding=(16, 12))
    table_area.grid(row=2, column=0, sticky="ew")
    table_area.columnconfigure(0, weight=1)

    # Controls row with section title (left) and refresh button (right)
    controls = ttk.Frame(table_area)
    controls.grid(row=0, column=0, sticky="ew")
    controls.columnconfigure(0, weight=1)
    controls.columnconfigure(1, weight=0)

    section_title = ttk.Label(controls, text="Batches", font=("Segoe UI", 12, "bold"))
    section_title.grid(row=0, column=0, sticky="w")

    refresh_btn = ttk.Button(controls, text="↻", width=3, command=lambda: refresh_batches_async(root))
    refresh_btn.grid(row=0, column=1, sticky="e")
    ToolTip(refresh_btn, "Refresh - Update the batch job lists with current status")

    # Notebook with two tabs
    notebook = ttk.Notebook(table_area)
    notebook.grid(row=1, column=0, sticky="ew")

    ongoing_tab, tree_ongoing = make_tab_with_tree(notebook)
    done_tab, tree_done = make_tab_with_tree(notebook)

    notebook.add(ongoing_tab, text="Ongoing")
    notebook.add(done_tab, text="Done")

    # --- Context menus for rows ---
    # Ongoing tab: "Cancel"
    ongoing_menu = tk.Menu(root, tearoff=False)

    def _on_cancel():
        sel = tree_ongoing.selection()
        if sel:
            values = tree_ongoing.item(sel[0], "values")
            cancel_batch_async(root, values[0])  # values[0] is the batch ID

    ongoing_menu.add_command(label="Cancel", command=_on_cancel)

    # Done tab: "Download"
    done_menu = tk.Menu(root, tearoff=False)

    def _on_download():
        sel = tree_done.selection()
        if sel:
            values = tree_done.item(sel[0], "values")
            call_batch_download_async(root, values[0])  # values[0] is the batch ID

    done_menu.add_command(label="Download", command=_on_download)

    # Bind right-clicks
    tree_ongoing.bind("<Button-3>", lambda e: popup_menu(e, tree_ongoing, ongoing_menu))
    tree_done.bind("<Button-3>", lambda e: popup_menu(e, tree_done, done_menu))
    # Optional: Control-click as an extra trigger
    tree_ongoing.bind("<Control-Button-1>", lambda e: popup_menu(e, tree_ongoing, ongoing_menu))
    tree_done.bind("<Control-Button-1>", lambda e: popup_menu(e, tree_done, done_menu))

    # Save references on root
    root.tree_ongoing = tree_ongoing
    root.tree_done = tree_done

    # Initial load
    refresh_batches_async(root)
    center_window(root, *WINDOW_SIZE)


if __name__ == "__main__":
    r = tk.Tk()
    build_ui(r)
    r.mainloop()
