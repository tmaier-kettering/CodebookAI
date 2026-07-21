"""
UI helper functions for widget creation and menu management.

This module provides helper functions for creating common UI components
and managing context menus and popup displays.
"""

import tkinter as tk
from tkinter import ttk


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