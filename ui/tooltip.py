"""
Tooltip widget for providing hover help text on buttons and widgets.

This module provides a simple tooltip implementation that creates popup
help text when hovering over widgets.
"""

import tkinter as tk


class ToolTip:
    """
    Simple tooltip widget for providing hover help text on buttons and widgets.

    This class creates a small popup tooltip that appears when the mouse
    hovers over a widget and disappears when the mouse leaves.
    """

    def __init__(self, widget: tk.Widget, text: str):
        """
        Initialize tooltip for a widget.

        Args:
            widget: The tkinter widget to attach the tooltip to
            text: The text to display in the tooltip
        """
        self.widget = widget
        self.text = text
        self.tooltip_window = None

        # Bind hover events
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)

    def _on_enter(self, event=None):
        """Show tooltip when mouse enters widget."""
        self._show_tooltip()

    def _on_leave(self, event=None):
        """Hide tooltip when mouse leaves widget."""
        self._hide_tooltip()

    def _show_tooltip(self):
        """Create and display the tooltip window."""
        if self.tooltip_window:
            return

        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 20

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background="lightyellow",
            relief="solid",
            borderwidth=1,
            font=("Arial", 9)
        )
        label.pack()

    def _hide_tooltip(self):
        """Destroy the tooltip window."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None