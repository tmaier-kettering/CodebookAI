"""
Tabular data loading utilities for various file formats.

This module provides functions for loading data from Excel, CSV, TSV, and TXT files
with automatic format detection and delimiter sniffing capabilities.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

# Optional pandas for robust Excel/CSV reading; gracefully degrade if unavailable
try:
    import pandas as _pd  # type: ignore
except Exception:
    _pd = None  # Falls back to csv module for text; Excel requires pandas


def is_excel(path: str) -> bool:
    """Check if a file path has an Excel extension."""
    return Path(path).suffix.lower() in {".xlsx", ".xls"}


def is_text_table(path: str) -> bool:
    """Check if a file path has a text table extension."""
    return Path(path).suffix.lower() in {".csv", ".tsv", ".txt"}


def read_excel(path: str, max_rows: Optional[int] = None) -> list[list[str]]:
    """
    Read an Excel file and return rows as list of string lists.
    
    Args:
        path: Path to the Excel file
        max_rows: Maximum number of rows to read (None for all)
        
    Returns:
        List of rows, where each row is a list of string values
        
    Raises:
        RuntimeError: If pandas is not available or reading fails
    """
    if _pd is None:
        raise RuntimeError("Reading Excel requires pandas. Please install pandas.")
    try:
        df = _pd.read_excel(path, nrows=max_rows)
    except Exception as e:
        raise RuntimeError(f"Failed to read Excel: {e}")
    return [[("" if _pd.isna(v) else str(v)) for v in row] for row in df.itertuples(index=False, name=None)]


def sniff_delimiter(sample: str) -> str:
    """
    Detect the delimiter used in a text sample.
    
    Args:
        sample: Text sample to analyze
        
    Returns:
        The detected delimiter character
    """
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", "\t", ";", "|"])
        return dialect.delimiter
    except Exception:
        return "\t" if sample.count("\t") > sample.count(",") else ","


def read_text_table(path: str, max_rows: Optional[int] = None) -> list[list[str]]:
    """
    Read a delimited text file (CSV, TSV, TXT) and return rows as list of string lists.
    
    Args:
        path: Path to the text file
        max_rows: Maximum number of rows to read (None for all)
        
    Returns:
        List of rows, where each row is a list of string values
        
    Raises:
        RuntimeError: If reading fails
    """
    def _read_with(file, enc=None):
        if enc:
            fh = open(file, "r", encoding=enc, newline="")
        else:
            fh = open(file, "r", newline="")
        with fh as f:
            sample = f.read(4096)
            f.seek(0)
            delimiter = sniff_delimiter(sample)
            reader = csv.reader(f, delimiter=delimiter)
            rows: list[list[str]] = []
            for i, row in enumerate(reader):
                rows.append([str(c) for c in row])
                if max_rows is not None and i + 1 >= max_rows:
                    break
            return rows

    try:
        return _read_with(path, enc="utf-8")
    except UnicodeDecodeError:
        return _read_with(path, enc=None)
    except Exception as e:
        raise RuntimeError(f"Failed to read delimited text: {e}")


def load_tabular(path: str, max_rows: Optional[int] = None) -> list[list[str]]:
    """
    Load tabular data from a file, automatically detecting the format.
    
    Args:
        path: Path to the file
        max_rows: Maximum number of rows to read (None for all)
        
    Returns:
        List of rows, where each row is a list of string values
        
    Raises:
        RuntimeError: If the file type is unsupported or reading fails
    """
    if is_excel(path):
        return read_excel(path, max_rows=max_rows)
    if is_text_table(path):
        return read_text_table(path, max_rows=max_rows)
    if _pd is not None:
        try:
            df = _pd.read_csv(path, nrows=max_rows)
            return [[("" if _pd.isna(v) else str(v)) for v in row] for row in df.itertuples(index=False, name=None)]
        except Exception:
            pass
    raise RuntimeError("Unsupported file type. Please select CSV/TSV/TXT or Excel (.xlsx/.xls).")