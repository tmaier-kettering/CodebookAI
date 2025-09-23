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

# Import and run the main UI
import tkinter as tk
from ui.main_window import build_ui

def _warm_models_cache():
    try:
        preload_models()
    except Exception:
        pass  # Non-fatal; Settings will still have the fallback list

if __name__ == "__main__":
    threading.Thread(target=_warm_models_cache, daemon=True).start()
    root = tk.Tk()
    build_ui(root)
    root.mainloop()