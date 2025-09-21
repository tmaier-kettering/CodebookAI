import threading
import tkinter as tk
from tkinter import ttk, messagebox
from settings_window import SettingsWindow

import live_processing.live_method
from batch_processing import batch_method
from batch_processing.batch_method import list_batches

APP_TITLE = "CodebookAI"
WINDOW_SIZE = (1000, 620)  # width, height
TABLE_HEIGHT_ROWS = 12


def center_window(win: tk.Tk, width: int, height: int) -> None:
    """Center the window on the current screen."""
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw // 2) - (width // 2)
    y = (sh // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


def populate_treeview(tree: ttk.Treeview, columns: tuple[str, ...], rows: list[tuple]) -> None:
    """Configure columns and fill the Treeview with tuple rows."""
    tree["columns"] = columns
    tree["show"] = "headings"
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="w")

    # Clear existing rows
    for iid in tree.get_children():
        tree.delete(iid)

    # Insert new rows
    for row in rows:
        tree.insert("", "end", values=row)


def call_batch_async(parent: tk.Tk) -> None:
    """Run batch_method() on a background thread, report errors to the UI."""
    def _worker():
        try:
            result = batch_method.send_batch(root)
            parent.after(0, lambda: print("batch_method finished:", result))
        except Exception as e:
            parent.after(0, lambda: messagebox.showerror("Batch Error", str(e)))
    threading.Thread(target=_worker, daemon=True).start()


def call_batch_download_async(parent: tk.Tk, batch_id: str) -> None:
    """Download batch results on a background thread, report errors to the UI."""
    def _worker():
        try:
            batch_method.get_batch_results(batch_id)
            parent.after(0, lambda: print("Download finished for batch:", batch_id))
        except Exception as e:
            parent.after(0, lambda: messagebox.showerror("Download Error", str(e)))
    threading.Thread(target=_worker, daemon=True).start()


def refresh_batches_async(parent: tk.Tk) -> None:
    """Fetch ongoing & done batches on a background thread and populate both tabs."""
    def _worker():
        try:
            ongoing_batches, done_batches = list_batches()

            def _update_ui():
                cols = ("id", "status", "created_at")
                populate_treeview(parent.tree_ongoing, cols, ongoing_batches)
                populate_treeview(parent.tree_done, cols, done_batches)

            parent.after(0, _update_ui)
        except Exception as e:
            parent.after(0, lambda: messagebox.showerror("Refresh Error", str(e)))
    threading.Thread(target=_worker, daemon=True).start()


def cancel_batch_async(parent: tk.Tk, batch_id: str) -> None:
    """Cancel a batch on a background thread, report errors to the UI."""
    def _worker():
        try:
            batch_method.cancel_batch(batch_id)
            parent.after(0, lambda: print("Cancel finished for batch:", batch_id))
        except Exception as e:
            parent.after(0, lambda: messagebox.showerror("Cancel Error", str(e)))
    threading.Thread(target=_worker, daemon=True).start()


def _make_tab_with_tree(parent_frame: ttk.Frame) -> tuple[ttk.Frame, ttk.Treeview]:
    """Helper to create a Treeview + horizontal scrollbar in a tab frame."""
    tab_inner = ttk.Frame(parent_frame)
    tab_inner.columnconfigure(0, weight=1)

    columns = ("id", "status", "created_at")
    tree = ttk.Treeview(tab_inner, columns=columns, show="headings", height=TABLE_HEIGHT_ROWS)
    for c in columns:
        tree.heading(c, text=c)
        tree.column(c, width=250 if c == "id" else 160, anchor="w")

    h_scroll = ttk.Scrollbar(tab_inner, orient="horizontal", command=tree.xview)
    tree.configure(xscrollcommand=h_scroll.set)

    tree.grid(row=0, column=0, sticky="ew")
    h_scroll.grid(row=1, column=0, sticky="ew")
    return tab_inner, tree


def _popup_menu(event: tk.Event, tree: ttk.Treeview, menu: tk.Menu) -> None:
    """Right-click helper: focus the row under cursor and show the menu."""
    iid = tree.identify_row(event.y)
    if iid:
        tree.selection_set(iid)
        tree.focus(iid)
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()


def _popup_menu_below_widget(widget: tk.Widget, menu: tk.Menu) -> None:
    """Show a menu directly below a widget (used for the Tools button)."""
    widget.update_idletasks()
    x = widget.winfo_rootx()
    y = widget.winfo_rooty() + widget.winfo_height()
    try:
        menu.tk_popup(x, y)
    finally:
        menu.grab_release()


def build_ui(root: tk.Tk) -> None:
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

    def _on_live_process():
        live_processing.live_method.send_live_call(root)
        pass

    def _on_sample():
        # TODO: hook up "Sample" action here
        # e.g., open a sample dialog or load sample data
        pass

    def _on_calc_irr():
        # TODO: hook up "Calculate Interrater Reliability" action here
        # e.g., open IRR calculator dialog
        pass

    tools_menu.add_command(label="Live Process", command=_on_live_process)
    # tools_menu.add_command(label="Sample", command=_on_sample)
    # tools_menu.add_command(label="Calculate Interrater Reliability", command=_on_calc_irr)

    tools_btn = ttk.Button(header, text="🛠", width=3,
                           command=lambda: _popup_menu_below_widget(tools_btn, tools_menu))
    tools_btn.grid(row=0, column=0, sticky="w")

    # Title (center)
    title_lbl = ttk.Label(header, text=APP_TITLE, font=("Segoe UI", 18, "bold"))
    title_lbl.grid(row=0, column=1, sticky="n", pady=(2, 0))

    # Settings (right)
    settings_btn = ttk.Button(header, text="⚙", width=3, command=lambda: SettingsWindow(root))
    settings_btn.grid(row=0, column=2, sticky="ne")

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

    refresh_btn = ttk.Button(controls, text="↻", width=3, command=lambda: refresh_batches_async(root))
    refresh_btn.grid(row=0, column=2, sticky="e", padx=(8, 0))

    # Notebook with two tabs
    notebook = ttk.Notebook(table_area)
    notebook.grid(row=1, column=0, sticky="ew")

    ongoing_tab, tree_ongoing = _make_tab_with_tree(notebook)
    done_tab, tree_done = _make_tab_with_tree(notebook)

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
    tree_ongoing.bind("<Button-3>", lambda e: _popup_menu(e, tree_ongoing, ongoing_menu))
    tree_done.bind("<Button-3>", lambda e: _popup_menu(e, tree_done, done_menu))
    # Optional: Control-click as an extra trigger
    tree_ongoing.bind("<Control-Button-1>", lambda e: _popup_menu(e, tree_ongoing, ongoing_menu))
    tree_done.bind("<Control-Button-1>", lambda e: _popup_menu(e, tree_done, done_menu))

    # Save references on root
    root.tree_ongoing = tree_ongoing
    root.tree_done = tree_done

    # Initial load
    refresh_batches_async(root)


if __name__ == "__main__":
    root = tk.Tk()
    build_ui(root)
    root.mainloop()
