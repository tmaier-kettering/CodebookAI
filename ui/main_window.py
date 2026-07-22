"""
Main window GUI for CodebookAI text classification application.

This module provides the primary user interface for the CodebookAI application,
including batch job management, live processing controls, and settings access.
The interface displays all batch jobs in one sortable/filterable table with a
detail pane (see ui/batches_view.py).

Top menu bar structure:
  File > Settings, Exit
  Data Prep > Sample
  LLM Tools > New Task (blank Task Builder), Presets > {built-in presets}
  Data Analysis > Reliability Statistics, Correlogram
  Help > Help Docs, Report a bug
"""

import sys, os
import tkinter as tk
from pathlib import Path
from tkinter import ttk
import webbrowser

from asset_path import asset_path
from core.presets import PRESETS
from live_processing.correlogram import open_correlogram_wizard
from live_processing.reliability_calculator import open_reliability_wizard
from live_processing.sampler import sample_data

# Handle imports based on how the script is run
try:
    from settings_window import SettingsWindow
    from tooltip import ToolTip
    from ui_utils import center_window, save_window_geometry, restore_window_geometry
    from batches_view import BatchesPanel
    from batch_operations import refresh_batches_async
    from task_builder import open_task_builder
except ImportError:  # fallback when running as a package (ui.*)
    from ui.settings_window import SettingsWindow
    from ui.tooltip import ToolTip
    from ui.ui_utils import center_window, save_window_geometry, restore_window_geometry
    from ui.batches_view import BatchesPanel
    from ui.batch_operations import refresh_batches_async
    from ui.task_builder import open_task_builder

APP_TITLE = "CodebookAI"
APP_SUBTITLE = "A qualitative research tool based on OpenAI's Playground API."
WINDOW_SIZE = (1000, 620)  # width, height
MAIN_WINDOW_GEOMETRY_KEY = "main_window_geometry"


def _open_help_docs():
    webbrowser.open("https://github.com/tmaier-kettering/CodebookAI?tab=readme-ov-file#readme")

def _open_report_bug():
    webbrowser.open("https://github.com/tmaier-kettering/CodebookAI/issues/new")


def build_ui(root: tk.Tk) -> None:
    """
    Build and configure the main application user interface.

    This function creates the complete UI layout including:
    - Header with app title & subtitle
    - Top menubar for navigation and actions
    - A single sortable/filterable batches table with a detail pane
    - Refresh control and a status-aware right-click menu for batch operations

    Args:
        root: The main Tkinter window to build the UI in
    """
    root.title(APP_TITLE)
    try:
        # .ico files are only natively supported by iconbitmap on Windows;
        # this raises TclError on Linux/macOS Tk builds.
        root.iconbitmap(asset_path("app.ico"))
    except tk.TclError:
        pass

    # ===== Top-level grid: header, spacer, table area =====
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=0)  # header
    root.rowconfigure(1, weight=0)  # spacer/filler (kept for compatibility)
    root.rowconfigure(2, weight=1)  # table area now grows with the window

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

    def _on_exit():
        save_window_geometry(root, MAIN_WINDOW_GEOMETRY_KEY)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_exit)

    # File
    file_menu = tk.Menu(menubar, tearoff=False)
    file_menu.add_command(label="Settings", command=lambda: SettingsWindow(root))
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=_on_exit)
    menubar.add_cascade(label="File", menu=file_menu)

    # Data Prep
    data_prep_menu = tk.Menu(menubar, tearoff=False)
    data_prep_menu.add_command(label="Sample", command=lambda: sample_data(root))
    menubar.add_cascade(label="Data Prep", menu=data_prep_menu)

    # LLM Tools > New Task / Presets
    # The old six hardcoded tools (single/multi/keyword x live/batch) are gone --
    # one Task Builder window covers all of it. Presets just pre-fill the builder.
    llm_tools_menu = tk.Menu(menubar, tearoff=False)
    llm_tools_menu.add_command(label="New Task", command=lambda: open_task_builder(root))

    presets_menu = tk.Menu(llm_tools_menu, tearoff=False)
    for key, (display_name, factory) in PRESETS.items():
        presets_menu.add_command(
            label=display_name,
            command=lambda factory=factory: open_task_builder(root, factory()),
        )
    llm_tools_menu.add_cascade(label="Presets", menu=presets_menu)
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
    table_area.grid(row=2, column=0, sticky="nsew")
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

    # Single merged, sortable/filterable table with a detail pane and a
    # status-aware right-click menu (Cancel / Download / Rerun).
    batches_panel = BatchesPanel(table_area)
    batches_panel.grid(row=1, column=0, sticky="nsew")
    table_area.rowconfigure(1, weight=1)
    root.batches_panel = batches_panel

    # Initial load
    refresh_batches_async(root)
    if not restore_window_geometry(root, MAIN_WINDOW_GEOMETRY_KEY):
        center_window(root, *WINDOW_SIZE)


if __name__ == "__main__":
    r = tk.Tk()
    build_ui(r)
    r.mainloop()
