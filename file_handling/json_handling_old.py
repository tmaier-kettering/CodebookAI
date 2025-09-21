from __future__ import annotations
import io, json
from typing import Iterable, List, Sequence
from pathlib import Path


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


def generate_batch_jsonl(
    labels: Sequence[str],
    quotes: Sequence[str],
    out_path: str | Path = "batchinput.jsonl",
    *,
    model: str = "gpt-5",
    custom_id_prefix: str = "quote",
) -> Path:
    """
    Create a JSONL batch file for the Responses API, one request per quote.
    Returns the Path to the created file.

    Parameters
    ----------
    labels : list[str]
        Allowed label names (e.g. ["positive","neutral","negative"]).
    quotes : list[str]
        Text snippets to classify (first column of your quotes CSV).
    out_path : str | Path
        Destination .jsonl file path.
    model : str
        The model to use for EVERY line in the batch file.
    custom_id_prefix : str
        Prefix for the per-line custom_id (e.g., "quote-00001").
    """
    labels = _normalize_str_list(labels)
    quotes = _normalize_str_list(quotes)

    if not labels:
        raise ValueError("labels is empty after normalization.")
    if not quotes:
        raise ValueError("quotes is empty after normalization.")

    # Build the exact schema you already use in live mode
    schema = build_schema(list(labels))

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for i, quote in enumerate(quotes, start=1):
            # Mirror your live prompt
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
                    "model": model,
                    "input": [
                        # You can add your system message here if you use one in live mode.
                        # For safety, keep it strict and JSON-only:
                        {
                            "role": "system",
                            "content": "You are a strict text classifier. Respond ONLY with JSON that matches the provided schema."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        },
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

            f.write(json.dumps(line, ensure_ascii=False) + "\n")

    return out_path.resolve()


def generate_batch_jsonl_bytes(
    labels: Sequence[str],
    quotes: Sequence[str],
    *,
    model: str = "gpt-5",
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
                "model": model,
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