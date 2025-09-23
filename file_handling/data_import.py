"""
Universal tabular import with a small 'Import Wizard' UI + nickname selector.

This module has been refactored into smaller, focused components for better maintainability:
- tabular_loaders.py: File loading and format detection
- tk_utils.py: Tkinter utility functions  
- preview_components.py: UI components for data preview
- import_dialog.py: Main import dialog logic

This file now serves as a compatibility layer, importing from the refactored modules
while maintaining the same public API.

Public API:
    import_data(parent: Optional[tk.Misc]=None, title="Import Data") -> Optional[tuple[list[str], str]]
"""

from __future__ import annotations

from typing import Optional, Sequence

# Import the main function from the refactored import dialog module
try:
    from .import_dialog import import_data
except ImportError:
    # Fallback for running from file_handling directory
    from import_dialog import import_data

# Re-export utility functions for backward compatibility
try:
    from .tabular_loaders import (
        is_excel as _is_excel,
        is_text_table as _is_text_table, 
        read_excel as _read_excel,
        sniff_delimiter as _sniff_delimiter,
        read_text_table as _read_text_table,
        load_tabular as _load_tabular
    )
    from .tk_utils import (
        ensure_parent as _ensure_parent,
        safe_destroy as _safe_destroy
    )
    from .preview_components import RadioHeader as _RadioHeader
except ImportError:
    # Fallback for running from file_handling directory
    from tabular_loaders import (
        is_excel as _is_excel,
        is_text_table as _is_text_table,
        read_excel as _read_excel,
        sniff_delimiter as _sniff_delimiter,
        read_text_table as _read_text_table,
        load_tabular as _load_tabular
    )
    from tk_utils import (
        ensure_parent as _ensure_parent,
        safe_destroy as _safe_destroy
    )
    from preview_components import RadioHeader as _RadioHeader


# Make the main function available at module level (primary public API)
__all__ = ['import_data']
