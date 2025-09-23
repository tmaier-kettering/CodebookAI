"""
Tkinter utility functions for dialog management.

This module provides common utility functions for managing Tkinter dialogs
and windows, including parent handling and safe cleanup.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional


def ensure_parent(parent: Optional[tk.Misc]) -> tuple[tk.Misc, Optional[tk.Tk]]:
    """
    Ensure we have a valid parent widget for dialogs.
    
    If no parent is provided, creates a hidden root window.
    
    Args:
        parent: Optional parent widget
        
    Returns:
        Tuple of (parent_widget, optional_root_to_cleanup)
    """
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


def safe_destroy(maybe_root: Optional[tk.Tk]) -> None:
    """
    Safely destroy a Tkinter root window.
    
    Args:
        maybe_root: Root window to destroy, or None
    """
    if maybe_root is not None:
        try:
            maybe_root.destroy()
        except Exception:
            pass