#!/usr/bin/env python3
"""
Helper script to systematically migrate tkinter imports to customtkinter.
This script performs safe, automated migrations across the codebase.
"""

import os
import re
from pathlib import Path


# Mapping of tkinter imports to customtkinter equivalents
IMPORT_REPLACEMENTS = {
    r'import tkinter as tk\n': 'import tkinter as tk\nimport customtkinter as ctk\n',
    r'from tkinter import ttk, messagebox': 'from tkinter import ttk\nimport customtkinter as ctk\n# Import dialog wrappers\ntry:\n    from ui.dialogs import show_error, show_info, show_warning, ask_yes_no\nexcept ImportError:\n    from tkinter import messagebox\n    show_error = messagebox.showerror\n    show_info = messagebox.showinfo\n    show_warning = messagebox.showwarning\n    ask_yes_no = messagebox.askyesno',
    r'from tkinter import messagebox, filedialog': 'import tkinter as tk\nimport customtkinter as ctk\ntry:\n    from ui.dialogs import show_error, show_info, show_warning, ask_open_filename, ask_save_filename\nexcept ImportError:\n    from tkinter import messagebox, filedialog\n    show_error = messagebox.showerror\n    show_info = messagebox.showinfo\n    show_warning = messagebox.showwarning\n    ask_open_filename = filedialog.askopenfilename\n    ask_save_filename = filedialog.asksaveasfilename',
}

# Simple messagebox call replacements
MESSAGEBOX_REPLACEMENTS = {
    r'messagebox\.showerror\(': 'show_error(',
    r'messagebox\.showinfo\(': 'show_info(',
    r'messagebox\.showwarning\(': 'show_warning(',
    r'messagebox\.askyesno\(': 'ask_yes_no(',
    r'messagebox\.askokcancel\(': 'ask_ok_cancel(',
}

# Filedialog call replacements  
FILEDIALOG_REPLACEMENTS = {
    r'filedialog\.askopenfilename\(': 'ask_open_filename(',
    r'filedialog\.asksaveasfilename\(': 'ask_save_filename(',
    r'filedialog\.askdirectory\(': 'ask_directory(',
}


def migrate_file(filepath: Path, dry_run: bool = True) -> tuple[bool, str]:
    """
    Migrate a single Python file to use customtkinter patterns.
    
    Returns:
        (changed, report_message)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        # Apply import replacements
        for old_pattern, new_pattern in IMPORT_REPLACEMENTS.items():
            if re.search(old_pattern, content):
                content = re.sub(old_pattern, new_pattern, content)
                changes.append(f"  - Updated import: {old_pattern[:50]}...")
        
        # Apply messagebox replacements
        for old_pattern, new_func in MESSAGEBOX_REPLACEMENTS.items():
            matches = re.findall(old_pattern, content)
            if matches:
                content = re.sub(old_pattern, new_func, content)
                changes.append(f"  - Replaced {len(matches)} messagebox calls")
        
        # Apply filedialog replacements
        for old_pattern, new_func in FILEDIALOG_REPLACEMENTS.items():
            matches = re.findall(old_pattern, content)
            if matches:
                content = re.sub(old_pattern, new_func, content)
                changes.append(f"  - Replaced {len(matches)} filedialog calls")
        
        if content != original_content:
            if not dry_run:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            report = f"✓ {filepath}\n" + "\n".join(changes)
            return True, report
        else:
            return False, f"  {filepath} - No changes needed"
            
    except Exception as e:
        return False, f"✗ {filepath} - Error: {e}"


def main():
    """Main migration script."""
    import sys
    
    dry_run = '--execute' not in sys.argv
    
    if dry_run:
        print("=" * 60)
        print("DRY RUN MODE - No files will be modified")
        print("Run with --execute to apply changes")
        print("=" * 60)
    
    repo_root = Path(__file__).parent
    python_files = list(repo_root.rglob("*.py"))
    python_files = [f for f in python_files if '.git' not in str(f) and '__pycache__' not in str(f)]
    
    # Exclude already migrated files
    exclude_files = {'dialogs.py', 'theme_config.py', 'migrate_helper.py'}
    python_files = [f for f in python_files if f.name not in exclude_files]
    
    changed_files = []
    unchanged_files = []
    
    for filepath in sorted(python_files):
        changed, report = migrate_file(filepath, dry_run=dry_run)
        if changed:
            changed_files.append(report)
        else:
            unchanged_files.append(report)
    
    print("\n" + "=" * 60)
    print(f"MIGRATION SUMMARY")
    print("=" * 60)
    
    if changed_files:
        print(f"\n{len(changed_files)} files would be changed:" if dry_run else f"\n{len(changed_files)} files changed:")
        for report in changed_files:
            print(report)
    
    print(f"\n{len(unchanged_files)} files unchanged")
    
    print("\n" + "=" * 60)
    if dry_run:
        print("Run with --execute to apply these changes")
    else:
        print("Migration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
