"""
UI helper functions for widget creation and menu management.

This module provides helper functions for creating common UI components
and managing context menus and popup displays.
"""

import tkinter as tk
from tkinter import ttk

# Constants for UI components
TABLE_HEIGHT_ROWS = 12


def make_tab_with_tree(parent_frame: ttk.Frame) -> tuple[ttk.Frame, ttk.Treeview]:
    """
    Create a Treeview widget with horizontal scrollbar inside a tab frame.

    Args:
        parent_frame: The parent frame to contain the tree and scrollbar

    Returns:
        Tuple of (tab_inner_frame, treeview_widget)
    """
    tab_inner = ttk.Frame(parent_frame)
    tab_inner.columnconfigure(0, weight=1)

    columns = ("id", "status", "created_at", "model", "type", "dataset(s)")
    tree = ttk.Treeview(tab_inner, columns=columns, show="headings", height=TABLE_HEIGHT_ROWS)
    for c in columns:
        tree.heading(c, text=c)
        tree.column(c, width=tab_inner.winfo_width()//len(columns), anchor="w")

    h_scroll = ttk.Scrollbar(tab_inner, orient="horizontal", command=tree.xview)
    tree.configure(xscrollcommand=h_scroll.set)

    tree.grid(row=0, column=0, sticky="ew")
    h_scroll.grid(row=1, column=0, sticky="ew")
    return tab_inner, tree


def popup_menu(event: tk.Event, tree: ttk.Treeview, menu: tk.Menu) -> None:
    """
    Handle right-click context menu display for tree items.

    This function focuses the row under the cursor and displays the context menu.

    Args:
        event: The mouse click event
        tree: The Treeview widget that was clicked
        menu: The context menu to display
    """
    iid = tree.identify_row(event.y)
    if iid:
        tree.selection_set(iid)
        tree.focus(iid)
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()


def popup_menu_below_widget(widget: tk.Widget, menu: tk.Menu) -> None:
    """
    Display a context menu directly below a widget.

    This is used for dropdown-style menus attached to buttons.

    Args:
        widget: The widget to position the menu below
        menu: The menu to display
    """
    widget.update_idletasks()
    x = widget.winfo_rootx()
    y = widget.winfo_rooty() + widget.winfo_height()
    try:
        menu.tk_popup(x, y)
    finally:
        menu.grab_release()