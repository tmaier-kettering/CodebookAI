"""
Main window GUI for CodebookAI text classification application.

This module provides the primary user interface for the CodebookAI application,
including batch job management, live processing controls, and settings access.
The interface displays ongoing and completed batch jobs in tabbed tables.
"""

import tkinter as tk
from tkinter import ttk

# Handle imports based on how the script is run
try:
    from settings_window import SettingsWindow
    from tooltip import ToolTip
    from ui_utils import center_window
    from ui_helpers import make_tab_with_tree, popup_menu, popup_menu_below_widget
    from batch_operations import call_batch_async, refresh_batches_async, call_batch_download_async, cancel_batch_async
except ImportError:
    from ui.settings_window import SettingsWindow
    from ui.tooltip import ToolTip
    from ui.ui_utils import center_window
    from ui.ui_helpers import make_tab_with_tree, popup_menu, popup_menu_below_widget
    from ui.batch_operations import call_batch_async, refresh_batches_async, call_batch_download_async, cancel_batch_async

try:
    import live_processing.multi_label_live
    import live_processing.single_label_live
    import live_processing.keyword_extraction_live
    import interrater_reliability
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import live_processing.multi_label_live
    import live_processing.single_label_live
    import live_processing.keyword_extraction_live
    import interrater_reliability

APP_TITLE = "CodebookAI"
WINDOW_SIZE = (1000, 620)  # width, height


def build_ui(root: tk.Tk) -> None:
    """
    Build and configure the main application user interface.

    This function creates the complete UI layout including:
    - Header with tools button, title, and settings button
    - Tabbed interface for ongoing and completed batch jobs
    - Control buttons for creating new batches and refreshing
    - Context menus for batch management operations

    Args:
        root: The main Tkinter window to build the UI in
    """
    root.title(APP_TITLE)
    center_window(root, *WINDOW_SIZE)

    # Grid: header, spacer, tabs+controls
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=0)
    root.rowconfigure(1, weight=1)
    root.rowconfigure(2, weight=0)

    # Header
    header = ttk.Frame(root, padding=(16, 12))
    header.grid(row=0, column=0, sticky="ew")
    # Now with three columns: tools button (left), title (center grows), settings (right)
    header.columnconfigure(0, weight=0)
    header.columnconfigure(1, weight=1)
    header.columnconfigure(2, weight=0)

    # --- Tools button + dropdown menu (🛠) ---
    tools_menu = tk.Menu(root, tearoff=False)

    def _single_label_live_call():
        live_processing.single_label_live.single_label_pipeline(root)
        pass

    def _multi_label_live_call():
        live_processing.multi_label_live.multi_label_pipeline(root)
        pass

    def _keyword_extraction_live_call():
        live_processing.keyword_extraction_live.keyword_extraction_pipeline(root)

    def _on_sample():
        # TODO: hook up "Sample" action here
        # e.g., open a sample dialog or load sample data
        pass

    def _on_calc_irr():
        # Hook up "Calculate Interrater Reliability" action
        interrater_reliability.calculate_interrater_reliability(root)

    tools_menu.add_command(label="Single Label Live Call", command=_single_label_live_call)
    tools_menu.add_command(label="Multi Label Live Call", command=_multi_label_live_call)
    tools_menu.add_command(label="Keyword Extraction Live Call", command=_keyword_extraction_live_call)
    # tools_menu.add_command(label="Sample", command=_on_sample)
    tools_menu.add_command(label="Calculate Interrater Reliability", command=_on_calc_irr)

    tools_btn = ttk.Button(header, text="🛠", width=3,
                           command=lambda: popup_menu_below_widget(tools_btn, tools_menu))
    tools_btn.grid(row=0, column=0, sticky="w")
    ToolTip(tools_btn, "Tools menu - Access live processing and other utilities")

    # Title (center)
    title_lbl = ttk.Label(header, text=APP_TITLE, font=("Segoe UI", 18, "bold"))
    title_lbl.grid(row=0, column=1, sticky="n", pady=(2, 0))

    # Settings (right)
    settings_btn = ttk.Button(header, text="⚙", width=3, command=lambda: SettingsWindow(root))
    settings_btn.grid(row=0, column=2, sticky="ne")
    ToolTip(settings_btn, "Settings - Configure API key, model, and other preferences")

    # Table area
    table_area = ttk.Frame(root, padding=(16, 12))
    table_area.grid(row=2, column=0, sticky="ew")
    table_area.columnconfigure(0, weight=1)

    # Controls row
    controls = ttk.Frame(table_area)
    controls.grid(row=0, column=0, sticky="ew")
    controls.columnconfigure(0, weight=1)
    controls.columnconfigure(1, weight=1)
    controls.columnconfigure(2, weight=1)

    add_btn = ttk.Button(controls, text="＋", width=3, command=lambda: call_batch_async(root))
    add_btn.grid(row=0, column=0, sticky="w", padx=(0, 8))
    ToolTip(add_btn, "Create new batch - Start a new text classification batch job")

    refresh_btn = ttk.Button(controls, text="↻", width=3, command=lambda: refresh_batches_async(root))
    refresh_btn.grid(row=0, column=2, sticky="e", padx=(8, 0))
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
        pass
    ongoing_menu.add_command(label="Cancel", command=_on_cancel)

    # Done tab: "Download"
    done_menu = tk.Menu(root, tearoff=False)
    def _on_download():
        sel = tree_done.selection()
        if sel:
            values = tree_done.item(sel[0], "values")
            call_batch_download_async(root, values[0])  # values[0] is the batch ID
        pass
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

