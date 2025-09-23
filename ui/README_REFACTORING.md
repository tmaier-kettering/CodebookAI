# UI Module Refactoring Documentation

## Overview
The original `main_window.py` file was refactored from 431 lines to 185 lines (57% reduction) by splitting functionality into focused modules.

## Refactored Modules

### `tooltip.py` (68 lines)
- **Purpose**: Tooltip widget for hover help text
- **Contains**: `ToolTip` class
- **Dependencies**: `tkinter` only

### `ui_utils.py` (49 lines)
- **Purpose**: Common UI utility functions
- **Contains**: 
  - `center_window()` - Centers a window on screen
  - `populate_treeview()` - Populates treeview widgets with data
- **Dependencies**: `tkinter`, `tkinter.ttk`

### `ui_helpers.py` (78 lines)
- **Purpose**: UI component creation and menu management
- **Contains**:
  - `make_tab_with_tree()` - Creates treeview tabs
  - `popup_menu()` - Handles right-click context menus
  - `popup_menu_below_widget()` - Shows dropdown menus
- **Dependencies**: `tkinter`, `tkinter.ttk`

### `batch_operations.py` (101 lines)
- **Purpose**: Asynchronous batch processing operations
- **Contains**:
  - `call_batch_async()` - Creates new batch jobs
  - `call_batch_download_async()` - Downloads batch results
  - `refresh_batches_async()` - Refreshes batch status
  - `cancel_batch_async()` - Cancels batch jobs
- **Dependencies**: `threading`, `tkinter`, `batch_processing`, `ui_utils`

### `main_window.py` (185 lines, reduced from 431)
- **Purpose**: Main UI construction and coordination
- **Contains**: 
  - `build_ui()` - Main UI builder function
  - Application constants (`APP_TITLE`, `WINDOW_SIZE`)
  - Entry point (`if __name__ == "__main__"`)
- **Dependencies**: All refactored modules plus live processing modules

## Import Strategy
Each module uses a dual import strategy to work both when:
1. Running from the repository root: `from ui.module import function`
2. Running from the ui directory: `from module import function`

## Benefits
- **Maintainability**: Smaller, focused files are easier to understand and modify
- **Reusability**: Components can be imported and used by other modules
- **Testing**: Individual components can be tested in isolation
- **Collaboration**: Multiple developers can work on different aspects without conflicts
- **No Circular Dependencies**: Clean import hierarchy prevents import issues

## Original vs. Refactored Structure

**Original:**
- `main_window.py` (431 lines) - Everything in one file

**Refactored:**
- `main_window.py` (185 lines) - Core UI coordination
- `tooltip.py` (68 lines) - Tooltip functionality
- `ui_utils.py` (49 lines) - Utility functions
- `ui_helpers.py` (78 lines) - UI helpers
- `batch_operations.py` (101 lines) - Async operations

**Total lines remain similar** (431 → 481), but **modularity and maintainability greatly improved**.