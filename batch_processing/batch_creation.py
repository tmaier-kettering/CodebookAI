"""
JSON schema handling and batch file generation for OpenAI text classification.

This module provides utilities for creating JSON schemas that enforce structured
responses from OpenAI models, and for generating JSONL batch files for processing
multiple text classification requests efficiently.
"""

from __future__ import annotations
import io, json
from enum import Enum
from io import BytesIO
from typing import Optional, List
import tkinter as tk
from pydantic import BaseModel, ConfigDict, Field

from file_handling.data_conversion import make_str_enum
from file_handling.data_import import import_data
from settings.config import model


def forbid_additional_props(schema: dict) -> dict:
    """Recursively set additionalProperties:false on every object schema."""
    if not isinstance(schema, dict):
        return schema

    # If this schema node is an object, set additionalProperties: false
    if schema.get("type") == "object":
        schema.setdefault("properties", {})
        schema["additionalProperties"] = False

        # Recurse into each property
        for prop_schema in schema.get("properties", {}).values():
            forbid_additional_props(prop_schema)

        # Recurse into patternProperties (rare but safe)
        for prop_schema in schema.get("patternProperties", {}).values():
            forbid_additional_props(prop_schema)

    # If it's an array, recurse into "items"
    if schema.get("type") == "array" and "items" in schema:
        forbid_additional_props(schema["items"])

    # oneOf/anyOf/allOf branches
    for key in ("oneOf", "anyOf", "allOf"):
        if key in schema and isinstance(schema[key], list):
            for s in schema[key]:
                forbid_additional_props(s)

    return schema


def generate_single_label_batch(labels, quotes) -> BytesIO | None:
    """
    Create a JSONL batch as bytes, in memory (no disk writes).
    Returns a BytesIO whose .name is set to 'batchinput.jsonl'.
    """
    labels_enum = make_str_enum("Label", labels)

    class LabeledQuote(BaseModel):
        label: labels_enum  # STRICT: must be one of labels
        model_config = ConfigDict(use_enum_values=True, extra='forbid')

    SCHEMA = LabeledQuote.model_json_schema()
    STRICT_SCHEMA = forbid_additional_props(SCHEMA)

    buf = io.BytesIO()
    # Give the buffer a filename so the API knows its type
    buf.name = "batchinput.jsonl"

    lines = []
    for i, q in enumerate(quotes, 1):
        lines.append({
            "custom_id": f"quote-{i:05d}",
            "method": "POST",
            "url": "/v1/responses",
            "body": {
                "model": model,
                "input": [
                    {"role": "user",
                     "content": f"Label this quote with exactly one label from the allowed set.\nQuote: {q}"}
                ],
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "LabeledQuote",
                        "schema": STRICT_SCHEMA,
                        "strict": True
                    }
                },
                "metadata": {"quote": q}
            }
        })

    for line in lines:
        buf.write((json.dumps(line, ensure_ascii=False) + "\n").encode("utf-8"))

    buf.seek(0)
    return buf


def generate_multi_label_batch(labels, quotes) -> BytesIO | None:
    """
    Create a JSONL batch as bytes, in memory (no disk writes).
    Returns a BytesIO whose .name is set to 'batchinput.jsonl'.
    """
    labels_enum = make_str_enum("Label", labels)

    class LabeledQuoteMulti(BaseModel):
        label: List[labels_enum] = Field(..., min_items=1)
        model_config = ConfigDict(use_enum_values=True, extra='forbid')

    SCHEMA = LabeledQuoteMulti.model_json_schema()
    STRICT_SCHEMA = forbid_additional_props(SCHEMA)

    buf = io.BytesIO()
    # Give the buffer a filename so the API knows its type
    buf.name = "batchinput.jsonl"

    lines = []
    for i, q in enumerate(quotes, 1):
        lines.append({
            "custom_id": f"quote-{i:05d}",
            "method": "POST",
            "url": "/v1/responses",
            "body": {
                "model": model,
                "input": [
                    {"role": "user",
                     "content": "Label this quote with labels from the allowed set only. \n"
                            f"Allowed: {', '.join(labels)}\nQuote: {q}"}
                ],
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "LabeledQuoteMulti",
                        "schema": STRICT_SCHEMA,
                        "strict": True
                    }
                },
                "metadata": {"quote": q}
            }
        })

    for line in lines:
        buf.write((json.dumps(line, ensure_ascii=False) + "\n").encode("utf-8"))

    buf.seek(0)
    return buf


def generate_keyword_extraction_batch(texts) -> BytesIO | None:
    """
    Create a JSONL batch as bytes, in memory (no disk writes).
    Returns a BytesIO whose .name is set to 'batchinput.jsonl'.
    """
    class KeywordExtraction(BaseModel):
        keywords: list[str] = Field(..., min_items=1)
        model_config = ConfigDict(extra='forbid')

    SCHEMA = KeywordExtraction.model_json_schema()
    STRICT_SCHEMA = forbid_additional_props(SCHEMA)

    buf = io.BytesIO()
    # Give the buffer a filename so the API knows its type
    buf.name = "batchinput.jsonl"

    lines = []
    for i, txt in enumerate(texts, 1):
        lines.append({
            "custom_id": f"text-{i:05d}",
            "method": "POST",
            "url": "/v1/responses",
            "body": {
                "model": model,
                "input": [{"role": "system", "content": "You are an expert at structured data extraction."},
                    {"role": "user", "content": f"Extract the keywords from this text: {txt}"}
                ],
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "KeywordExtraction",
                        "schema": STRICT_SCHEMA,
                        "strict": True
                    }
                },
                "metadata": {"quote": txt}
            }
        })

    for line in lines:
        buf.write((json.dumps(line, ensure_ascii=False) + "\n").encode("utf-8"))

    buf.seek(0)
    return buf
