"""
Tests for file_handling/data_conversion.py

Covers:
- make_str_enum: creates valid Enum, handles unicode labels, rejects unknown values
- to_long_df: from dicts, from pydantic models, list-column explode, empty input,
              nested dicts, multi-label expansion
- join_datasets: None, string, bytes, iterable, mixed types
"""

import math
from enum import Enum

import pandas as pd
import pytest
from pydantic import BaseModel, ConfigDict

from file_handling.data_conversion import join_datasets, make_str_enum, to_long_df


# ---------------------------------------------------------------------------
# make_str_enum
# ---------------------------------------------------------------------------

class TestMakeStrEnum:
    def test_returns_enum_type(self, sample_labels):
        EnumCls = make_str_enum("Label", sample_labels)
        assert issubclass(EnumCls, Enum)

    def test_members_match_input(self, sample_labels):
        EnumCls = make_str_enum("Label", sample_labels)
        member_values = [m.value for m in EnumCls]
        assert sorted(member_values) == sorted(sample_labels)

    def test_name_is_set(self, sample_labels):
        EnumCls = make_str_enum("MySentiment", sample_labels)
        assert EnumCls.__name__ == "MySentiment"

    def test_member_access_by_value(self, sample_labels):
        EnumCls = make_str_enum("Label", sample_labels)
        assert EnumCls("positive").value == "positive"

    def test_single_label(self):
        EnumCls = make_str_enum("Label", ["only_label"])
        assert len(list(EnumCls)) == 1

    def test_unicode_labels(self):
        labels = ["positivo", "négative", "中立", "Ünïcödé"]
        EnumCls = make_str_enum("Label", labels)
        member_values = [m.value for m in EnumCls]
        assert "中立" in member_values
        assert "Ünïcödé" in member_values

    def test_label_with_spaces(self):
        labels = ["very positive", "somewhat negative", "totally neutral"]
        EnumCls = make_str_enum("Label", labels)
        assert EnumCls("very positive").value == "very positive"

    def test_pydantic_model_enforces_enum(self, sample_labels):
        """Enum produced by make_str_enum should integrate with pydantic validation."""
        LabelEnum = make_str_enum("Label", sample_labels)

        class Row(BaseModel):
            label: LabelEnum
            model_config = ConfigDict(use_enum_values=True)

        row = Row(label="positive")
        assert row.label == "positive"

    def test_pydantic_model_rejects_unknown_label(self, sample_labels):
        """An unknown label should fail pydantic validation."""
        from pydantic import ValidationError

        LabelEnum = make_str_enum("Label", sample_labels)

        class Row(BaseModel):
            label: LabelEnum
            model_config = ConfigDict(use_enum_values=True)

        with pytest.raises(ValidationError):
            Row(label="completely_unknown")


# ---------------------------------------------------------------------------
# to_long_df
# ---------------------------------------------------------------------------

class TestToLongDf:
    def test_from_plain_dicts(self):
        records = [{"label": "positive", "quote": "Good!"}, {"label": "negative", "quote": "Bad!"}]
        df = to_long_df(records)
        assert list(df.columns) == ["label", "quote"]
        assert df["label"].tolist() == ["positive", "negative"]

    def test_from_empty_list(self):
        df = to_long_df([])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_from_pydantic_models(self, sample_labels):
        LabelEnum = make_str_enum("Label", sample_labels)

        class Row(BaseModel):
            id: int
            label: LabelEnum
            model_config = ConfigDict(use_enum_values=True)

        rows = [Row(id=1, label="positive"), Row(id=2, label="negative")]
        df = to_long_df(rows)
        assert len(df) == 2
        assert "label" in df.columns
        assert df["label"].tolist() == ["positive", "negative"]

    def test_explodes_list_column(self):
        """Multi-label records should be exploded into one row per label."""
        records = [
            {"id": 1, "quote": "Good bad neutral", "label": ["positive", "negative"]},
            {"id": 2, "quote": "Just good", "label": ["positive"]},
        ]
        df = to_long_df(records)
        # Row 1 yields 2 exploded rows, row 2 yields 1 → total 3
        assert len(df) == 3
        assert set(df["label"]) == {"positive", "negative"}

    def test_flattens_nested_dicts(self):
        records = [{"meta": {"author": "Alice"}, "label": "positive"}]
        df = to_long_df(records)
        # json_normalize should create a 'meta.author' column
        assert "meta.author" in df.columns

    def test_single_record(self):
        df = to_long_df([{"label": "neutral"}])
        assert len(df) == 1
        assert df["label"].iloc[0] == "neutral"

    def test_nonascii_values_preserved(self):
        records = [{"label": "中立", "text": "日本語テキスト"}]
        df = to_long_df(records)
        assert df["label"].iloc[0] == "中立"
        assert df["text"].iloc[0] == "日本語テキスト"

    def test_repair_note_column_preserved(self):
        records = [{"label": "positive", "quote": "Good!", "repair_note": "Truncated JSON repaired"}]
        df = to_long_df(records)
        assert "repair_note" in df.columns
        assert df["repair_note"].iloc[0] == "Truncated JSON repaired"


# ---------------------------------------------------------------------------
# join_datasets
# ---------------------------------------------------------------------------

class TestJoinDatasets:
    def test_none_returns_empty_string(self):
        assert join_datasets(None) == ""

    def test_string_returned_as_is(self):
        assert join_datasets("my_dataset") == "my_dataset"

    def test_bytes_returned_as_is(self):
        # bytes is a Sequence but join_datasets returns it as-is (str/bytes check)
        result = join_datasets(b"raw")
        assert result == b"raw"

    def test_tuple_joined_with_comma(self):
        assert join_datasets(("labels", "quotes")) == "labels,quotes"

    def test_list_joined_with_comma(self):
        assert join_datasets(["a", "b", "c"]) == "a,b,c"

    def test_single_item_iterable(self):
        assert join_datasets(["only"]) == "only"

    def test_integer_converted_to_string(self):
        assert join_datasets(42) == "42"

    def test_generator_joined(self):
        result = join_datasets(x for x in ["x", "y"])
        assert result == "x,y"
