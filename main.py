#!/usr/bin/env python3
"""
Main entry point for CodebookAI application.

This script initializes and runs the CodebookAI text classification application.
"""

import sys
import os
import threading

from settings.models_registry import preload_models

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import CustomTkinter and initialize theme
import customtkinter as ctk
from ui.theme_config import initialize_theme

# Try to import TkinterDnD for drag-and-drop support
try:
    from tkinterdnd2 import TkinterDnD
    _HAS_DND = True
except ImportError:
    _HAS_DND = False

from ui.main_window import build_ui


def _warm_models_cache():
    """Preload models in background thread."""
    try:
        preload_models()
    except Exception:
        pass  # Non-fatal; Settings will still have the fallback list


if __name__ == "__main__":
    # Initialize theme before creating any widgets
    initialize_theme()
    
    # Start background model cache warming
    threading.Thread(target=_warm_models_cache, daemon=True).start()
    
    # Create root window with drag-and-drop support if available
    if _HAS_DND:
        # TkinterDnD doesn't support CTk directly, use compatibility mode
        root = TkinterDnD.Tk()
        # Apply CTk styling to the Tk window
        ctk.set_appearance_mode("System")
    else:
        root = ctk.CTk()
    
    build_ui(root)
    root.mainloop()