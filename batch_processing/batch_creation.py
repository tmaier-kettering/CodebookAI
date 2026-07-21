"""
JSONL batch file generation for OpenAI Structured Outputs requests.

This used to be three near-identical functions (generate_single_label_batch,
generate_multi_label_batch, generate_keyword_extraction_batch), each with its
own hardcoded prompt and Pydantic model. They're now one function driven by a
core.task.Task -- the prompt, the constant/per-row split, and the output
schema all come from the task instead of being baked in here.
"""

from __future__ import annotations

import io
import json
from io import BytesIO

from core.task import Task, build_request_params, build_strict_schema, render_prompt


def generate_batch(task: Task, rows: list[dict]) -> BytesIO:
    """
    Create a JSONL batch as bytes, in memory (no disk writes).
    One row -> one request, custom_id = "row-00001", "row-00002", ...
    (1-based, matching the row order of `rows`).

    Row data itself is NOT sent as request metadata -- OpenAI's metadata has
    a ~512 char/value limit that arbitrary carried columns could exceed.
    Carried columns are rejoined locally by row position after download
    (see batch_processing.batch_method).
    """
    schema = build_strict_schema(task)
    request_params = build_request_params(task)

    buf = io.BytesIO()
    buf.name = "batchinput.jsonl"

    for i, row in enumerate(rows, 1):
        messages = []
        if task.system:
            messages.append({"role": "system", "content": render_prompt(task, row, text=task.system)})
        messages.append({"role": "user", "content": render_prompt(task, row)})

        line = {
            "custom_id": f"row-{i:05d}",
            "method": "POST",
            "url": "/v1/responses",
            "body": {
                "input": messages,
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "TaskOutput",
                        "schema": schema,
                        "strict": True,
                    }
                },
                **request_params,
            },
        }
        buf.write((json.dumps(line, ensure_ascii=False) + "\n").encode("utf-8"))

    buf.seek(0)
    return buf
