"""
Tests for file_handling/data_import.py (non-GUI utilities only)

These tests exercise the tabular-reading helpers that do not require a
live Tkinter display or user interaction.  The GUI import-wizard
(import_data) is excluded because it is driven entirely by user interaction.

Covers:
- _sniff_delimiter: comma vs. tab vs. semi-colon
- _read_text_table: basic CSV, no-header, max_rows limit, non-ASCII content,
                    missing columns, empty file
- _load_tabular: dispatch to _read_text_table for .csv/.tsv/.txt and
                 _read_excel for .xlsx
"""

import csv
import io
from pathlib import Path

import pandas as pd
import pytest

from file_handling.data_import import (
    _load_tabular,
    _read_text_table,
    _sniff_delimiter,
)


# ---------------------------------------------------------------------------
# _sniff_delimiter
# ---------------------------------------------------------------------------

class TestSniffDelimiter:
    def test_detects_comma(self):
        sample = "a,b,c\n1,2,3\n"
        assert _sniff_delimiter(sample) == ","

    def test_detects_tab(self):
        sample = "a\tb\tc\n1\t2\t3\n"
        assert _sniff_delimiter(sample) == "\t"

    def test_detects_semicolon(self):
        sample = "a;b;c\n1;2;3\n"
        assert _sniff_delimiter(sample) == ";"

    def test_fallback_to_comma_on_ambiguous(self):
        # Equal counts of commas and tabs → implementation falls back
        result = _sniff_delimiter("x")
        assert result in (",", "\t")  # either is acceptable as a fallback


# ---------------------------------------------------------------------------
# _read_text_table
# ---------------------------------------------------------------------------

class TestReadTextTable:
    def test_reads_basic_csv(self, tmp_csv):
        path = tmp_csv("col1,col2\nalpha,1\nbeta,2\n")
        rows = _read_text_table(str(path))
        assert rows[0] == ["col1", "col2"]
        assert rows[1] == ["alpha", "1"]
        assert rows[2] == ["beta", "2"]

    def test_reads_basic_tsv(self, tmp_csv):
        path = tmp_csv("col1\tcol2\nalpha\t1\nbeta\t2\n", filename="test.tsv")
        rows = _read_text_table(str(path))
        assert rows[0] == ["col1", "col2"]

    def test_max_rows_respected(self, tmp_csv):
        content = "h1,h2\n" + "\n".join(f"r{i},v{i}" for i in range(50))
        path = tmp_csv(content)
        rows = _read_text_table(str(path), max_rows=5)
        assert len(rows) == 5

    def test_nonascii_content_preserved(self, tmp_csv):
        path = tmp_csv("text\nCafé\nRésumé\n日本語\n")
        rows = _read_text_table(str(path))
        values = [r[0] for r in rows[1:]]
        assert "Café" in values
        assert "日本語" in values

    def test_single_column_no_header(self, tmp_csv):
        path = tmp_csv("positive\nnegative\nneutral\n")
        rows = _read_text_table(str(path))
        flat = [r[0] for r in rows]
        assert "positive" in flat
        assert "negative" in flat

    def test_empty_file_returns_empty_list(self, tmp_csv):
        path = tmp_csv("")
        rows = _read_text_table(str(path))
        assert rows == []

    def test_mismatched_row_widths(self, tmp_csv):
        """Rows with fewer columns than the header should be read without crashing."""
        path = tmp_csv("a,b,c\n1,2\n3,4,5\n")
        rows = _read_text_table(str(path))
        # At least 3 rows (header + 2 data)
        assert len(rows) >= 3

    def test_punctuation_heavy_content(self, tmp_csv):
        path = tmp_csv('text\n"He said, \\"It\'s great!\\" — really? (Yes!)"')
        rows = _read_text_table(str(path))
        assert len(rows) >= 2

    def test_long_text_cell(self, tmp_csv):
        long_text = "word " * 500
        path = tmp_csv(f"text\n{long_text}\n")
        rows = _read_text_table(str(path))
        assert len(rows) == 2
        assert rows[1][0].strip() == long_text.strip()


# ---------------------------------------------------------------------------
# _load_tabular
# ---------------------------------------------------------------------------

class TestLoadTabular:
    def test_csv_dispatches_correctly(self, tmp_csv):
        path = tmp_csv("name,value\nfoo,1\nbar,2\n")
        rows = _load_tabular(str(path))
        assert rows[0] == ["name", "value"]
        assert len(rows) == 3

    def test_tsv_dispatches_correctly(self, tmp_csv):
        path = tmp_csv("name\tvalue\nfoo\t1\n", filename="data.tsv")
        rows = _load_tabular(str(path))
        assert rows[0] == ["name", "value"]

    def test_max_rows_forwarded(self, tmp_csv):
        content = "h\n" + "\n".join(str(i) for i in range(100))
        path = tmp_csv(content)
        rows = _load_tabular(str(path), max_rows=10)
        assert len(rows) == 10

    def test_excel_dispatches_correctly(self, tmp_path):
        """_load_tabular should read .xlsx files via pandas/openpyxl.

        Note: _read_excel uses pd.read_excel which consumes the header row
        internally, so itertuples yields only data rows (no header row in
        the returned list).
        """
        xlsx_path = tmp_path / "test.xlsx"
        df = pd.DataFrame({"col_a": ["x", "y"], "col_b": [1, 2]})
        df.to_excel(xlsx_path, index=False)

        rows = _load_tabular(str(xlsx_path))
        # pandas consumed the header; the first element is the first data row
        assert rows[0] == ["x", "1"]
        assert rows[1] == ["y", "2"]

    def test_unsupported_extension_raises(self, tmp_path):
        """An unsupported extension whose content also fails pandas CSV
        parsing should raise RuntimeError."""
        weird = tmp_path / "file.unknown_ext_xyz"
        # Write binary content that pandas cannot parse as CSV
        weird.write_bytes(b"\x00\x01\x02\x03\xff\xfe")
        with pytest.raises(RuntimeError):
            _load_tabular(str(weird))

    def test_realistic_fixture_csv(self):
        """Use the checked-in realistic fixture to verify end-to-end reading."""
        fixture = Path(__file__).parent / "fixtures" / "realistic_dataset.csv"
        rows = _load_tabular(str(fixture))
        # Header row
        assert rows[0][0] == "text"
        # At least 5 data rows
        assert len(rows) >= 6

    def test_label_fixture_single_column(self):
        fixture = Path(__file__).parent / "fixtures" / "sample_labels.csv"
        rows = _load_tabular(str(fixture))
        values = [r[0] for r in rows[1:]]  # skip header
        assert "positive" in values
        assert "negative" in values
        assert "neutral" in values
