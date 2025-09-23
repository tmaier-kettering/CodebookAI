# File Handling Module Refactoring Documentation

## Overview

The `data_import.py` file has been refactored from a monolithic 504-line file into multiple focused, maintainable modules. This refactoring improves code organization while preserving all existing functionality and maintaining backward compatibility.

## Refactored Modules

### `tabular_loaders.py` (107 lines)
- **Purpose**: File format detection and data loading utilities
- **Contains**:
  - `load_tabular()` - Main entry point for loading any supported format
  - `is_excel()`, `is_text_table()` - File type detection functions
  - `read_excel()`, `read_text_table()` - Format-specific readers
  - `sniff_delimiter()` - Automatic delimiter detection for text files
- **Dependencies**: `csv`, `pathlib`, `pandas` (optional)

### `tk_utils.py` (44 lines) 
- **Purpose**: Tkinter utility functions for dialog management
- **Contains**:
  - `ensure_parent()` - Parent widget validation and root creation
  - `safe_destroy()` - Safe cleanup of Tkinter windows
- **Dependencies**: `tkinter` only

### `preview_components.py` (180 lines)
- **Purpose**: UI components for data preview functionality
- **Contains**:
  - `RadioHeader` class - Scrollable radio button widget for column selection
  - `PreviewManager` class - Manages tabular data preview and display
- **Dependencies**: `tkinter`, `tkinter.ttk`

### `import_dialog.py` (302 lines)
- **Purpose**: Main import dialog coordination and logic
- **Contains**:
  - `import_data()` - Primary public API function
  - Dialog construction and event handling
  - Nickname management and validation
  - File processing and result extraction
- **Dependencies**: All refactored modules plus `tkinter`, `pathlib`

### `data_import.py` (50 lines, reduced from 504)
- **Purpose**: Backward compatibility layer and public API
- **Contains**:
  - Re-exports `import_data()` function
  - Compatibility imports for any legacy internal usage
  - Documentation explaining the refactoring
- **Dependencies**: All refactored modules

## Import Strategy

Each module uses a dual import strategy to work both when:
1. Running from the repository root: `from file_handling.module import function`
2. Running from the file_handling directory: `from module import function`

This ensures compatibility across different execution contexts.

## Benefits

- **Maintainability**: Smaller, focused files are easier to understand and modify
- **Reusability**: Components can be imported and used by other modules
- **Testing**: Individual components can be tested in isolation
- **Collaboration**: Multiple developers can work on different aspects without conflicts
- **No Circular Dependencies**: Clean import hierarchy prevents import issues
- **Backward Compatibility**: Existing code continues to work without changes

## Dependencies Analysis

### External Dependencies by Module:
- **tabular_loaders.py**: `csv`, `pathlib`, `pandas` (optional)
- **tk_utils.py**: `tkinter`
- **preview_components.py**: `tkinter`, `tkinter.ttk`
- **import_dialog.py**: `tkinter`, `tkinter.ttk`, `pathlib`
- **data_import.py**: None (compatibility layer)

### Usage by Other Modules:
- `batch_processing/batch_method.py`: Imports entire module as `data_import`
- `live_processing/*.py`: Imports `import_data` function directly

## Original vs. Refactored Structure

### Before:
```
file_handling/
├── data_import.py (504 lines)
    ├── Tkinter utilities (20 lines)
    ├── File loading functions (64 lines) 
    ├── RadioHeader widget (54 lines)
    └── Import dialog logic (366 lines)
```

### After:
```
file_handling/
├── tabular_loaders.py (107 lines)     # File loading utilities
├── tk_utils.py (44 lines)             # Tkinter utilities  
├── preview_components.py (180 lines)  # UI preview components
├── import_dialog.py (302 lines)       # Main dialog logic
└── data_import.py (50 lines)          # Compatibility layer
```

## Migration Notes

No code changes are required for existing modules that import from `data_import.py`. The `import_data` function continues to work exactly as before, with the same signature and behavior.

Internal functions that were previously available (prefixed with `_`) are now properly encapsulated within their respective modules and should not be accessed directly by external code.