"""
Message box and file dialog wrappers for CustomTkinter compatibility.

This module provides wrapper functions for messageboxes and file dialogs
that work seamlessly with CustomTkinter while maintaining familiar API.
"""

from tkinter import messagebox, filedialog
from typing import Optional, Literal


# ==================== Message Box Wrappers ====================

def show_info(title: str, message: str, **kwargs) -> str:
    """
    Display an informational message box.
    
    Args:
        title: The title of the message box
        message: The message to display
        **kwargs: Additional arguments passed to messagebox.showinfo
    
    Returns:
        String result from the message box
    """
    return messagebox.showinfo(title, message, **kwargs)


def show_warning(title: str, message: str, **kwargs) -> str:
    """
    Display a warning message box.
    
    Args:
        title: The title of the message box
        message: The message to display
        **kwargs: Additional arguments passed to messagebox.showwarning
    
    Returns:
        String result from the message box
    """
    return messagebox.showwarning(title, message, **kwargs)


def show_error(title: str, message: str, **kwargs) -> str:
    """
    Display an error message box.
    
    Args:
        title: The title of the message box
        message: The message to display
        **kwargs: Additional arguments passed to messagebox.showerror
    
    Returns:
        String result from the message box
    """
    return messagebox.showerror(title, message, **kwargs)


def ask_yes_no(title: str, message: str, **kwargs) -> bool:
    """
    Display a yes/no question message box.
    
    Args:
        title: The title of the message box
        message: The question to ask
        **kwargs: Additional arguments passed to messagebox.askyesno
    
    Returns:
        True if yes, False if no
    """
    return messagebox.askyesno(title, message, **kwargs)


def ask_ok_cancel(title: str, message: str, **kwargs) -> bool:
    """
    Display an OK/Cancel message box.
    
    Args:
        title: The title of the message box
        message: The message to display
        **kwargs: Additional arguments passed to messagebox.askokcancel
    
    Returns:
        True if OK, False if Cancel
    """
    return messagebox.askokcancel(title, message, **kwargs)


def ask_retry_cancel(title: str, message: str, **kwargs) -> bool:
    """
    Display a Retry/Cancel message box.
    
    Args:
        title: The title of the message box
        message: The message to display
        **kwargs: Additional arguments passed to messagebox.askretrycancel
    
    Returns:
        True if Retry, False if Cancel
    """
    return messagebox.askretrycancel(title, message, **kwargs)


def ask_question(title: str, message: str, **kwargs) -> str:
    """
    Display a question message box.
    
    Args:
        title: The title of the message box
        message: The question to ask
        **kwargs: Additional arguments passed to messagebox.askquestion
    
    Returns:
        'yes' or 'no'
    """
    return messagebox.askquestion(title, message, **kwargs)


# ==================== File Dialog Wrappers ====================

def ask_open_filename(title: str = "Open File", 
                      filetypes: Optional[list[tuple[str, str]]] = None,
                      initialdir: Optional[str] = None,
                      **kwargs) -> str:
    """
    Display a file open dialog.
    
    Args:
        title: The title of the dialog
        filetypes: List of (label, pattern) tuples for file filtering
        initialdir: Initial directory to show
        **kwargs: Additional arguments passed to filedialog.askopenfilename
    
    Returns:
        Selected file path, or empty string if cancelled
    """
    return filedialog.askopenfilename(
        title=title,
        filetypes=filetypes or [("All Files", "*.*")],
        initialdir=initialdir,
        **kwargs
    )


def ask_open_filenames(title: str = "Open Files",
                       filetypes: Optional[list[tuple[str, str]]] = None,
                       initialdir: Optional[str] = None,
                       **kwargs) -> tuple[str, ...]:
    """
    Display a file open dialog that allows multiple selection.
    
    Args:
        title: The title of the dialog
        filetypes: List of (label, pattern) tuples for file filtering
        initialdir: Initial directory to show
        **kwargs: Additional arguments passed to filedialog.askopenfilenames
    
    Returns:
        Tuple of selected file paths, or empty tuple if cancelled
    """
    return filedialog.askopenfilenames(
        title=title,
        filetypes=filetypes or [("All Files", "*.*")],
        initialdir=initialdir,
        **kwargs
    )


def ask_save_filename(title: str = "Save File",
                      filetypes: Optional[list[tuple[str, str]]] = None,
                      initialdir: Optional[str] = None,
                      defaultextension: Optional[str] = None,
                      **kwargs) -> str:
    """
    Display a file save dialog.
    
    Args:
        title: The title of the dialog
        filetypes: List of (label, pattern) tuples for file filtering
        initialdir: Initial directory to show
        defaultextension: Default file extension to append
        **kwargs: Additional arguments passed to filedialog.asksaveasfilename
    
    Returns:
        Selected file path, or empty string if cancelled
    """
    return filedialog.asksaveasfilename(
        title=title,
        filetypes=filetypes or [("All Files", "*.*")],
        initialdir=initialdir,
        defaultextension=defaultextension,
        **kwargs
    )


def ask_directory(title: str = "Select Directory",
                  initialdir: Optional[str] = None,
                  **kwargs) -> str:
    """
    Display a directory selection dialog.
    
    Args:
        title: The title of the dialog
        initialdir: Initial directory to show
        **kwargs: Additional arguments passed to filedialog.askdirectory
    
    Returns:
        Selected directory path, or empty string if cancelled
    """
    return filedialog.askdirectory(
        title=title,
        initialdir=initialdir,
        **kwargs
    )
