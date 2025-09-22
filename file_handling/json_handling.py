"""
JSON schema handling and batch file generation for OpenAI text classification.

This module provides utilities for creating JSON schemas that enforce structured
responses from OpenAI models, and for generating JSONL batch files for processing
multiple text classification requests efficiently.
"""

from __future__ import annotations
import io, json
from typing import Iterable, List, Sequence
from settings import config


def build_schema(allowed_labels: list[str]) -> dict:
    """
    Create a JSON schema for text classification responses.
    
    This schema enforces that OpenAI responses contain exactly the expected
    structure: a list of classifications with quote, label, and confidence.
    
    Args:
        allowed_labels: List of valid classification labels
        
    Returns:
        JSON schema dictionary that validates classification responses
    """
    item_schema = {
        "type": "object",
        "properties": {
            "quote": {"type": "string", "minLength": 1},
            "label": {"type": "string", "enum": allowed_labels},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        },
        "required": ["quote", "label", "confidence"],
        "additionalProperties": False
    }

    return {
        "type": "object",
        "properties": {
            "classifications": {
                "type": "array",
                "items": item_schema,
                "minItems": 1
            }
        },
        "required": ["classifications"],
        "additionalProperties": False
    }


def _normalize_str_list(items: Iterable[str]) -> List[str]:
    """
    Clean and filter a list of strings, removing empty/whitespace-only items.
    
    Args:
        items: Iterable of string-like items
        
    Returns:
        List of non-empty, stripped strings
    """
    return [str(x).strip() for x in items if str(x).strip()]


def generate_batch_jsonl_bytes(
    labels: Sequence[str],
    quotes: Sequence[str],
    *,
    custom_id_prefix: str = "quote",
) -> io.BytesIO:
    """
    Create a JSONL batch file for OpenAI batch processing API.
    
    This function generates a properly formatted JSONL file in memory that can
    be uploaded to OpenAI's batch processing API. Each line represents one
    text classification request with structured JSON schema validation.
    
    Args:
        labels: Sequence of allowed classification labels
        quotes: Sequence of text snippets to classify
        custom_id_prefix: Prefix for custom IDs in the batch (default: "quote")
        
    Returns:
        BytesIO buffer containing the JSONL batch file data
        
    Raises:
        ValueError: If labels or quotes are empty after normalization
        
    Note:
        The returned BytesIO has its .name set to 'batchinput.jsonl' for API compatibility.
    """
    # Normalize and validate inputs
    labels = [str(x).strip() for x in labels if str(x).strip()]
    quotes = [str(x).strip() for x in quotes if str(x).strip()]
    if not labels:
        raise ValueError("labels is empty after normalization.")
    if not quotes:
        raise ValueError("quotes is empty after normalization.")

    schema = build_schema(list(labels))

    # Create in-memory JSONL file
    buf = io.BytesIO()
    # Give the buffer a filename so the API knows its type
    buf.name = "batchinput.jsonl"

    # Generate one JSONL line per quote
    for i, quote in enumerate(quotes, start=1):
        prompt = (
            "Classify the text into exactly one of the allowed labels. Return JSON only."
            f"Allowed labels: {list(labels)}\n\n"
            f'Text for classification: "{quote}"'
        )
        
        # OpenAI batch API request format
        line = {
            "custom_id": f"{custom_id_prefix}-{i:05d}",
            "method": "POST",
            "url": "/v1/responses",
            "body": {
                "model": config.model,
                "input": [
                    {
                        "role": "system",
                        "content": "You are a strict text classifier. Respond ONLY with JSON that matches the provided schema."
                    },
                    {"role": "user", "content": prompt},
                ],
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "QuoteClassification",
                        "schema": schema,
                        "strict": True
                    }
                },
            },
        }
        buf.write((json.dumps(line, ensure_ascii=False) + "\n").encode("utf-8"))
    
    buf.seek(0)
    return buf