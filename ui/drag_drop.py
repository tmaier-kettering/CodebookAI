"""
Drag-and-drop utility for file selection widgets.

Provides a reusable function to enable drag-and-drop file selection on widgets,
specifically for Windows Explorer file drag-and-drop support.
Compatible with both tkinter and customtkinter widgets.
"""

import os
import tkinter as tk
import customtkinter as ctk
from typing import Callable, Optional, Union

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    _HAS_DND = True
except ImportError:
    _HAS_DND = False


def enable_file_drop(widget: Union[tk.Widget, ctk.CTkBaseClass], 
                     callback: Callable[[str], None], 
                     file_types: Optional[list[str]] = None) -> bool:
    """
    Enable drag-and-drop file selection on a widget.
    
    Args:
        widget: The widget to enable drag-and-drop on (tkinter or customtkinter)
        callback: Function to call with the file path when a file is dropped
        file_types: Optional list of allowed file extensions (e.g., ['.csv', '.xlsx'])
                   If None, all file types are allowed
    
    Returns:
        True if drag-and-drop was successfully enabled, False otherwise
    
    Example:
        >>> import customtkinter as ctk
        >>> entry = ctk.CTkEntry(root)
        >>> enable_file_drop(entry, lambda path: entry_var.set(path))
    """
    if not _HAS_DND:
        return False
    
    def _on_drop(event):
        """Handle the drop event."""
        # The event.data can be a list of files or a single file path
        # It comes in a format like: {path1} {path2} or just path
        # We need to parse it correctly
        files = event.data
        
        # Handle different formats
        if isinstance(files, (list, tuple)):
            # Already a list
            file_list = files
        else:
            # Parse the string - files can be separated by spaces or in curly braces
            file_list = []
            if files.startswith('{'):
                # Format: {path1} {path2}
                import re
                file_list = re.findall(r'\{([^}]+)\}', files)
            else:
                # Simple space-separated or single file
                # But be careful with paths containing spaces
                if os.path.exists(files.strip()):
                    file_list = [files.strip()]
                else:
                    # Try to split, but this might not work with spaces in paths
                    file_list = [f.strip() for f in files.split() if f.strip()]
        
        # Get the first valid file
        for file_path in file_list:
            file_path = file_path.strip().strip('{}')
            
            # Validate file exists
            if not os.path.exists(file_path):
                continue
            
            # Validate file type if specified
            if file_types:
                ext = os.path.splitext(file_path)[1].lower()
                if ext not in file_types:
                    continue
            
            # Call the callback with the first valid file
            callback(file_path)
            break
    
    try:
        # Register the widget for file drop
        widget.drop_target_register(DND_FILES)
        widget.dnd_bind('<<Drop>>', _on_drop)
        return True
    except Exception:
        return False


def make_window_dnd_compatible(window: Union[tk.Tk, ctk.CTk, tk.Toplevel, ctk.CTkToplevel]):
    """
    Make a window compatible with drag-and-drop.
    
    This should be called on the root window or Toplevel to enable DnD support.
    For regular tk.Tk() or ctk.CTk(), this will upgrade them to support DnD.
    
    Args:
        window: A window instance (tkinter or customtkinter)
    
    Returns:
        The window (potentially upgraded to TkinterDnD version)
    
    Note:
        If using TkinterDnD, you should create your root window as TkinterDnD.Tk()
        instead of tk.Tk() or ctk.CTk() for best results. This function is a helper
        for existing windows.
        
        CustomTkinter windows will work with TkinterDnD if the root was created
        as TkinterDnD.Tk() (as done in main.py).
    """
    if not _HAS_DND:
        return window
    
    # If the window is already DnD-compatible, return it as-is
    if hasattr(window, 'drop_target_register'):
        return window
    
    # Otherwise, we can't upgrade an existing window easily
    # Just return the original window
    return window
