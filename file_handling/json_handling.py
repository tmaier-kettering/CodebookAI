from __future__ import annotations
import io, json
from typing import Iterable, List, Sequence
from pathlib import Path
import config


def build_schema(allowed_labels: list[str]) -> dict:
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
    return [str(x).strip() for x in items if str(x).strip()]


def generate_batch_jsonl_bytes(
    labels: Sequence[str],
    quotes: Sequence[str],
    *,
    custom_id_prefix: str = "quote",
) -> io.BytesIO:
    """
    Create a JSONL batch as bytes, in memory (no disk writes).
    Returns a BytesIO whose .name is set to 'batchinput.jsonl'.
    """
    labels = [str(x).strip() for x in labels if str(x).strip()]
    quotes = [str(x).strip() for x in quotes if str(x).strip()]
    if not labels:
        raise ValueError("labels is empty after normalization.")
    if not quotes:
        raise ValueError("quotes is empty after normalization.")

    schema = build_schema(list(labels))

    buf = io.BytesIO()
    # Give the buffer a filename so the API knows its type
    buf.name = "batchinput.jsonl"

    for i, quote in enumerate(quotes, start=1):
        prompt = (
            "Classify the text into exactly one of the allowed labels. Return JSON only."
            f"Allowed labels: {list(labels)}\n\n"
            f'Text for classification: "{quote}"'
        )
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