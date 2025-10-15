# Visual Comparison: Before and After Drag-and-Drop Implementation

## Overview
This document shows the visual changes in each file selection dialog.

---

## 1. Import Data Wizard (`file_handling/data_import.py`)

### Before
```
┌─────────────────────────────────────────────────────────────┐
│ Import Data                                            [X]   │
├─────────────────────────────────────────────────────────────┤
│ Use this window as an import wizard.                        │
│                                                              │
│ File: [_________________________________] [Browse…]         │
│                                                              │
│ ☑ File has headers (skip first row)                         │
│                                                              │
│ Select exactly one column to import using round buttons.    │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ ○ Column1  ○ Column2  ○ Column3  ○ Column4          │   │
│ └──────────────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────────────┐   │
│ │  Preview Table                                       │   │
│ │  ────────────────────────────────────────────────────│   │
│ │  Row 1 data...                                       │   │
│ │  Row 2 data...                                       │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│                                    [Cancel]  [Import]       │
└─────────────────────────────────────────────────────────────┘
```

### After (With Drag-and-Drop)
```
┌─────────────────────────────────────────────────────────────┐
│ Import Data                                            [X]   │
├─────────────────────────────────────────────────────────────┤
│ Use this window as an import wizard.                        │
│                                                              │
│ File: [_________________________________] [Browse…]         │
│       ↑ DRAG FILES HERE! (CSV, Excel, TXT, TSV)            │
│       ↑ Automatically validates file types                  │
│                                                              │
│ ☑ File has headers (skip first row)                         │
│                                                              │
│ Select exactly one column to import using round buttons.    │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ ○ Column1  ○ Column2  ○ Column3  ○ Column4          │   │
│ └──────────────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────────────┐   │
│ │  Preview Table                                       │   │
│ │  ────────────────────────────────────────────────────│   │
│ │  Row 1 data...                                       │   │
│ │  Row 2 data...                                       │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│                                    [Cancel]  [Import]       │
└─────────────────────────────────────────────────────────────┘
```

**What Changed:**
- Entry field now accepts drag-and-drop
- File type filtering active (only .csv, .xlsx, .xls, .txt, .tsv)
- No visual changes when not dragging
- Browse button unchanged and still works

---

## 2. Two-Page Dataset Wizard (`ui/two_page_wizard.py`)

### Before
```
┌─────────────────────────────────────────────────────────────┐
│ Dataset 1                                                    │
├─────────────────────────────────────────────────────────────┤
│ [Choose file…] ☑ Has header row                             │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Preview (top 5)                                      │   │
│ │ ────────────────────────────────────────────────────│   │
│ │  No file selected                                    │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ Select TEXT column:                                          │
│ [○ Column1  ○ Column2  ○ Column3]                           │
│                                                              │
│ Select LABEL column:                                         │
│ [○ Column1  ○ Column2  ○ Column3]                           │
│                                                              │
│                           [Cancel]  [◀ Back]  [Next ▶]     │
└─────────────────────────────────────────────────────────────┘
```

### After (With Drag-and-Drop)
```
┌─────────────────────────────────────────────────────────────┐
│ Dataset 1                                                    │
├─────────────────────────────────────────────────────────────┤
│ [Choose file…] ☑ Has header row                             │
│ (drag file here or use Choose file button)                  │
│  ↑ DRAG FILES HERE! Shows filename when dropped             │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Preview (top 5)                                      │   │
│ │ ────────────────────────────────────────────────────│   │
│ │  Drag a data file or click Choose file              │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ Select TEXT column:                                          │
│ [○ Column1  ○ Column2  ○ Column3]                           │
│                                                              │
│ Select LABEL column:                                         │
│ [○ Column1  ○ Column2  ○ Column3]                           │
│                                                              │
│                           [Cancel]  [◀ Back]  [Next ▶]     │
└─────────────────────────────────────────────────────────────┘
```

**What Changed:**
- Path label now shows hint text: "(drag file here or use Choose file button)"
- Label accepts drag-and-drop
- Shows filename after file is dropped
- File type filtering (CSV, TSV, TXT, Excel)
- Choose file button unchanged and still works

---

## 3. Data Sampler (`live_processing/sampler.py`)

### Before
```
┌─────────────────────────────────────────────────────────────┐
│ Sample Data                                                  │
├─────────────────────────────────────────────────────────────┤
│ Selected file:                                               │
│ [_________________________________] [Browse…]               │
│                                                              │
│ ☑ File has header row    Refresh                           │
│                                                              │
│ Sampling Mode:                                               │
│   ○ Number of rows: [100  ]                                 │
│   ● Percent:       [10.0 ]%                                 │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Preview (20 rows max)                                │   │
│ │ ────────────────────────────────────────────────────│   │
│ │  No file loaded                                      │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│                                    [Cancel]  [Sample]       │
└─────────────────────────────────────────────────────────────┘
```

### After (With Drag-and-Drop)
```
┌─────────────────────────────────────────────────────────────┐
│ Sample Data                                                  │
├─────────────────────────────────────────────────────────────┤
│ Selected file:                                               │
│ [_________________________________] [Browse…]               │
│  ↑ DRAG FILES HERE! (CSV, Excel, Parquet, etc.)            │
│                                                              │
│ ☑ File has header row    Refresh                           │
│                                                              │
│ Sampling Mode:                                               │
│   ○ Number of rows: [100  ]                                 │
│   ● Percent:       [10.0 ]%                                 │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Preview (20 rows max)                                │   │
│ │ ────────────────────────────────────────────────────│   │
│ │  Drag a file or click Browse                         │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│                                    [Cancel]  [Sample]       │
└─────────────────────────────────────────────────────────────┘
```

**What Changed:**
- Entry field accepts drag-and-drop
- File type filtering (.csv, .tsv, .tab, .xlsx, .xls, .parquet)
- File loads automatically when dropped
- Browse button unchanged and still works

---

## User Experience Flow

### Scenario 1: Using Drag-and-Drop (NEW!)
```
1. User opens Import Data dialog
   ↓
2. User has file open in Windows Explorer
   ↓
3. User clicks and holds the file
   ↓
4. User drags file over the entry field
   ↓
5. [Cursor changes - Windows shows copy icon]
   ↓
6. User releases mouse button (drops file)
   ↓
7. File path appears in entry field
   ↓
8. Preview loads automatically
   ↓
9. User continues with import
```

### Scenario 2: Using Browse Button (UNCHANGED)
```
1. User opens Import Data dialog
   ↓
2. User clicks [Browse…] button
   ↓
3. File dialog opens
   ↓
4. User navigates and selects file
   ↓
5. File path appears in entry field
   ↓
6. Preview loads automatically
   ↓
7. User continues with import
```

### Both methods work! User can choose whichever is more convenient.

---

## Code Changes Visualization

### Entry Widget - Before
```python
file_entry = ttk.Entry(dlg, textvariable=file_var, width=56)
file_entry.grid(row=1, column=1, padx=4, pady=4, sticky="we")
```

### Entry Widget - After
```python
file_entry = ttk.Entry(dlg, textvariable=file_var, width=56)
file_entry.grid(row=1, column=1, padx=4, pady=4, sticky="we")

# Enable drag-and-drop on the file entry
if enable_file_drop is not None:
    def _handle_drop(path):
        file_var.set(path)
        _refresh_preview()
    
    # Extract allowed extensions from filetypes
    allowed_extensions = []
    for name, pattern in filetypes:
        if pattern != "*.*":
            exts = pattern.replace("*", "").split()
            allowed_extensions.extend(exts)
    
    enable_file_drop(file_entry, _handle_drop, 
                    allowed_extensions if allowed_extensions else None)
```

**Only ~15 lines added per dialog! Minimal, surgical changes.**

---

## Summary

### Visual Impact
- ✅ No UI layout changes
- ✅ No new buttons or controls
- ✅ Existing controls unchanged
- ✅ Only functional enhancement (drag-and-drop)
- ✅ Optional hint text in wizard dialogs

### User Benefits
- ⚡ Faster file selection
- 👍 Familiar Windows behavior
- 🎯 More intuitive workflow
- 🔄 Browse buttons still work
- ✅ No learning curve

### Technical Quality
- 📦 Minimal code changes (~50 lines modified)
- 🔧 Reusable utility module
- ✅ File type validation
- 🔙 Backward compatible
- 📚 Well documented
