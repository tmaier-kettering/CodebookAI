# Drag-and-Drop File Selection

This document describes the drag-and-drop file selection feature added to CodebookAI.

## Overview

Users can now drag files from Windows Explorer directly into file selection areas in the following dialogs:
- **Import Data Wizard** (file_handling/data_import.py)
- **Two-Page Dataset Wizard** (ui/two_page_wizard.py)
- **Data Sampler** (live_processing/sampler.py)

## How to Use

1. **Open any dialog with file selection**
   - Import Data: File > Import Data (or use the import_data function)
   - Two-Page Wizard: When prompted to select datasets for reliability analysis or similar operations
   - Data Sampler: Data Prep > Sample

2. **Drag a file from Windows Explorer**
   - Locate your data file in Windows Explorer
   - Click and hold the file
   - Drag it over the file selection area (entry field or label)
   - Release the mouse button to drop the file

3. **The file path will be automatically populated**
   - The file will be loaded just as if you had used the "Browse" button
   - File type validation is performed automatically
   - Only supported file types are accepted

## Supported File Types

The drag-and-drop feature validates file types based on the context:

### Import Data Wizard
- Excel: `.xlsx`, `.xls`
- CSV: `.csv`
- TSV: `.tsv`
- Text: `.txt`

### Two-Page Wizard
- Excel: `.xlsx`, `.xls`, `.xlsm`
- CSV: `.csv`
- TSV: `.tsv`
- Text: `.txt`

### Data Sampler
- Excel: `.xlsx`, `.xls`
- CSV: `.csv`
- TSV/Tab: `.tsv`, `.tab`
- Parquet: `.parquet`

## Technical Details

### Dependencies
- `tkinterdnd2>=0.4.0` - Provides native drag-and-drop support on Windows

### Fallback Behavior
If the `tkinterdnd2` library is not available:
- The application will start normally with regular `tk.Tk()` window
- All "Browse" buttons continue to work as before
- Drag-and-drop functionality is silently disabled
- No errors or warnings are shown to the user

### Implementation
The drag-and-drop support is implemented using:
1. A reusable utility module: `ui/drag_drop.py`
2. The `enable_file_drop()` function that can be applied to any tkinter widget
3. File type filtering to ensure only appropriate files are accepted
4. Integration with existing file loading logic for consistency

## For Developers

### Adding Drag-and-Drop to New Widgets

To add drag-and-drop support to a new file selection widget:

```python
# Import the utility
from ui.drag_drop import enable_file_drop

# Create your file entry or label widget
file_entry = ttk.Entry(parent, textvariable=file_var)
file_entry.grid(...)

# Define a callback for when a file is dropped
def handle_drop(file_path):
    file_var.set(file_path)
    load_file(file_path)  # Your file loading logic

# Enable drag-and-drop with optional file type filtering
allowed_extensions = ['.csv', '.xlsx', '.txt']
enable_file_drop(file_entry, handle_drop, allowed_extensions)
```

### Testing

Since drag-and-drop requires a GUI environment:
1. Run the application on Windows: `python main.py`
2. Open any dialog with file selection
3. Drag a file from Windows Explorer onto the file selection area
4. Verify the file path is populated and the file loads correctly
5. Test with both valid and invalid file types
6. Verify the Browse button still works

### Architecture

The implementation follows these principles:
- **Minimal changes**: Only added drag-and-drop, didn't modify existing code
- **Backward compatible**: Works with or without tkinterdnd2
- **Consistent**: Uses same file loading logic as Browse buttons
- **Reusable**: Single utility function works for all widgets
- **Type-safe**: File type validation prevents errors

## Troubleshooting

**Drag-and-drop doesn't work:**
- Ensure `tkinterdnd2` is installed: `pip install tkinterdnd2`
- Verify you're running on Windows (primary support platform)
- Check that the file type is supported for that dialog

**Files are rejected when dropped:**
- Check the file extension matches the supported types
- Try using the Browse button to verify the file can be loaded

**Application doesn't start:**
- The application should start even without tkinterdnd2
- Check Python and dependency versions match requirements.txt
