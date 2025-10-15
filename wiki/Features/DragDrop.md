# Drag-and-Drop File Selection Guide

## Overview

CodebookAI now supports drag-and-drop file selection! You can drag files directly from Windows Explorer into file selection areas throughout the application, making it faster and more convenient to work with your data files.

![Drag and Drop Feature](../../assets/drag-drop-demo.gif)
*Note: Demo GIF to be added*

## Where You Can Use Drag-and-Drop

Drag-and-drop works in all dialogs that allow file selection:

### 1. Import Data Wizard
- **Location**: File menu > Import Data (or when prompted to import data)
- **Where to drop**: The file path entry field
- **Accepted files**: CSV, TSV, TXT, Excel (.xlsx, .xls)

### 2. Two-Page Dataset Wizard
- **Location**: Data Analysis > Reliability Statistics (when selecting datasets)
- **Where to drop**: The file path label area (shows hint text)
- **Accepted files**: CSV, TSV, TXT, Excel (.xlsx, .xls, .xlsm)

### 3. Data Sampler
- **Location**: Data Prep > Sample
- **Where to drop**: The file path entry field
- **Accepted files**: CSV, TSV, Tab, Excel, Parquet files

## How to Use

1. **Open a dialog with file selection**
   - Use the menu to access any feature that requires file selection
   - You'll see either an entry field or a label where you can drop files

2. **Drag your file**
   - Locate your data file in Windows Explorer
   - Click and hold on the file
   - Drag it over to the CodebookAI window
   - Hover over the file selection area (entry field or label)

3. **Drop the file**
   - Release the mouse button
   - The file path will be automatically populated
   - The file will be loaded and previewed (if applicable)

4. **Alternative: Use the Browse button**
   - Drag-and-drop is optional - all Browse buttons still work
   - Choose whichever method is more convenient for you

## Visual Guide

### Import Data Wizard
```
┌─────────────────────────────────────────────────┐
│ Import Data Wizard                              │
├─────────────────────────────────────────────────┤
│ File: [________________________] [Browse…]      │
│       👆 Drop files here!                       │
│                                                 │
│ ☑ File has headers (skip first row)            │
│                                                 │
│ [Preview Table]                                 │
└─────────────────────────────────────────────────┘
```

### Two-Page Wizard
```
┌─────────────────────────────────────────────────┐
│ Dataset 1                                       │
├─────────────────────────────────────────────────┤
│ [Choose file…] ☑ Has header row                 │
│ (drag file here or use Choose file button)     │
│ 👆 Drop files here!                             │
│                                                 │
│ [Preview Table]                                 │
└─────────────────────────────────────────────────┘
```

## File Type Validation

The drag-and-drop feature automatically validates file types:

- ✅ **Accepted**: Files with supported extensions are loaded immediately
- ❌ **Rejected**: Files with unsupported extensions are silently ignored
- 🔍 **Smart**: Only shows file types relevant to each dialog

This prevents accidental loading of incompatible files.

## Benefits

- **Faster workflow**: No need to navigate through file browser dialogs
- **Visual feedback**: See your file names as you work
- **Reduced clicks**: Save time when working with multiple files
- **Familiar**: Works just like drag-and-drop in other Windows applications

## Troubleshooting

### Drag-and-drop doesn't work
- **Check dependencies**: Ensure `tkinterdnd2` is installed
  ```bash
  pip install tkinterdnd2
  ```
- **Platform**: This feature is optimized for Windows
- **Fallback**: Use the Browse button if drag-and-drop is unavailable

### File is rejected when dropped
- **File type**: Check that your file has a supported extension
- **Corruption**: Try opening the file in Excel/text editor first
- **Alternative**: Use the Browse button to see detailed error messages

### Application doesn't start
- The app works even without `tkinterdnd2`
- Drag-and-drop will be disabled, but Browse buttons work
- Check that all other dependencies are installed

## Technical Notes

### Dependencies
- **tkinterdnd2**: Provides native Windows drag-and-drop support
- **Version**: 0.4.0 or higher
- **Installation**: Automatically installed with `pip install -r requirements.txt`

### Backward Compatibility
- Application works with or without `tkinterdnd2`
- If library is missing, drag-and-drop is silently disabled
- All existing Browse button functionality is preserved
- No changes to file loading or validation logic

### Platform Support
- **Windows**: Full support (primary platform)
- **macOS**: May work with tkinterdnd2 installed
- **Linux**: Limited support, depends on desktop environment

## Developer Information

For developers who want to add drag-and-drop to new widgets, see:
- Source code: `ui/drag_drop.py`
- Implementation examples: `file_handling/data_import.py`, `ui/two_page_wizard.py`
- Test script: `test_drag_drop_gui.py` (run on Windows)

Example usage:
```python
from ui.drag_drop import enable_file_drop

# Create your widget
file_entry = ttk.Entry(parent, textvariable=file_var)

# Define drop handler
def handle_drop(file_path):
    file_var.set(file_path)
    load_file(file_path)

# Enable drag-and-drop with file type filtering
allowed_types = ['.csv', '.xlsx', '.txt']
enable_file_drop(file_entry, handle_drop, allowed_types)
```

## Feedback

If you encounter issues or have suggestions:
1. Check existing GitHub issues
2. Create a new issue with:
   - Windows version
   - Python version
   - Steps to reproduce
   - Expected vs actual behavior

---

**Related Documentation:**
- [Main README](../../README.md)
- [File Menu](../File/File.md)
- [Data Prep](../DataPrep/DataPrep.md)
