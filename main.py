#!/usr/bin/env python3
"""
Main entry point for CodebookAI application.

This script initializes and runs the CodebookAI text classification application.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import and run the main UI
import tkinter as tk
from ui.main_window import build_ui

if __name__ == "__main__":
    root = tk.Tk()
    build_ui(root)
    root.mainloop()