from __future__ import annotations

import io
import json
import re
from collections.abc import Sequence
from copy import deepcopy
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, ValidationError, create_model

from batch_processing.batch_creation import forbid_additional_props
from batch_processing.batch_error_handling import handle_batch_fail
from file_handling.data_conversion import make_str_enum
from file_handling.data_import import (
    ImportedDataset,
    _load_tabular,
    normalize_tabular_rows,
    rows_to_records,
)
from prompt_editor.config import (
    AdditionalSourceDefinition,
    BatchJobRecord,
    BatchRowContext,
    OutputDefinition,
    PlaceholderBinding,
    PrimarySourceDefinition,
    PromptTemplateConfig,
)
from prompt_editor.storage import get_project_key, load_batch_job, save_batch_job
from settings import secrets_store
from ui.progress_ui import ProgressController
from openai import OpenAI

TOKEN_PATTERN = re.compile(r"<([a-zA-Z0-9_]+)>")


class _StructuredResponseModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")


def get_client() -> OpenAI:
    api_key = secrets_store.load_api_key()
    if not api_key:
        raise Exception("OpenAI API key not configured. Please set it in Settings.")
    return OpenAI(api_key=api_key)


def get_batch_status(batch_id: str) -> Any:
    client = get_client()
    return client.batches.retrieve(batch_id)


def make_source_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "source"


def build_primary_source(imported: ImportedDataset, passthrough_columns: list[str] | None = None) -> PrimarySourceDefinition:
    selected_column = imported.selected_column_name
    passthrough = passthrough_columns or ([selected_column] if selected_column else [])
    return PrimarySourceDefinition(
        dataset_name=imported.dataset_name,
        file_path=imported.file_path,
        has_headers=imported.has_headers,
        selected_column=selected_column,
        available_columns=imported.columns,
        passthrough_columns=passthrough,
        rows=deepcopy(imported.rows),
    )


def build_additional_source(
    imported: ImportedDataset,
    source_id: str | None = None,
    render_mode: str = "unique_values",
) -> AdditionalSourceDefinition:
    return AdditionalSourceDefinition(
        source_id=source_id or make_source_id(imported.dataset_name),
        dataset_name=imported.dataset_name,
        file_path=imported.file_path,
        has_headers=imported.has_headers,
        selected_column=imported.selected_column_name,
        available_columns=imported.columns,
        render_mode=render_mode,
        rows=deepcopy(imported.rows),
    )


def load_source_rows(file_path: str, has_headers: bool) -> tuple[list[str], list[dict[str, str]]]:
    rows = _load_tabular(file_path)
    columns, body = normalize_tabular_rows(rows, has_headers)
    return columns, rows_to_records(columns, body)


def hydrate_config(config: PromptTemplateConfig) -> PromptTemplateConfig:
    hydrated = config.model_copy(deep=True)

    if hydrated.primary_source.file_path and not hydrated.primary_source.rows:
        columns, rows = load_source_rows(hydrated.primary_source.file_path, hydrated.primary_source.has_headers)
        hydrated.primary_source.available_columns = columns
        hydrated.primary_source.rows = rows

    for source in hydrated.additional_sources:
        if source.file_path and not source.rows:
            columns, rows = load_source_rows(source.file_path, source.has_headers)
            source.available_columns = columns
            source.rows = rows

    return hydrated


def _find_source(config: PromptTemplateConfig, source_id: str) -> PrimarySourceDefinition | AdditionalSourceDefinition:
    if source_id == config.primary_source.source_id:
        return config.primary_source
    for source in config.additional_sources:
        if source.source_id == source_id:
            return source
    raise ValueError(f"Unknown source binding: {source_id}")


def list_available_tokens(config: PromptTemplateConfig) -> list[str]:
    return [binding.token for binding in config.placeholder_bindings]


def _non_empty_values(rows: list[dict[str, str]], column_name: str) -> list[str]:
    values: list[str] = []
    for row in rows:
        value = str(row.get(column_name, "")).strip()
        if value:
            values.append(value)
    return values


def enum_values_for_output(
    config: PromptTemplateConfig,
    output_def: OutputDefinition,
    enum_values_override: dict[str, list[str]] | None = None,
) -> list[str]:
    if enum_values_override and output_def.name in enum_values_override:
        values = enum_values_override[output_def.name]
        if values:
            return values

    if not output_def.enum_source_id:
        raise ValueError(f"Output '{output_def.name}' is missing an enum source.")

    source = _find_source(config, output_def.enum_source_id)
    column_name = output_def.enum_source_column or source.selected_column
    if not column_name:
        raise ValueError(f"Output '{output_def.name}' has no enum source column.")
    if column_name not in source.available_columns and source.available_columns:
        raise ValueError(f"Column '{column_name}' is not available in source '{source.dataset_name}'.")

    seen: set[str] = set()
    ordered: list[str] = []
    for value in _non_empty_values(source.rows, column_name):
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    if not ordered:
        raise ValueError(f"Output '{output_def.name}' resolved to an empty allowed-label set.")
    return ordered


def build_response_model(
    config: PromptTemplateConfig,
    enum_values_override: dict[str, list[str]] | None = None,
) -> tuple[type[BaseModel], dict, dict[str, list[str]]]:
    model_fields: dict[str, tuple[Any, Any]] = {}
    enum_cache: dict[str, list[str]] = {}

    model_outputs = [output for output in config.output_definitions if output.source_type == "model_output"]
    if not model_outputs:
        raise ValueError("Add at least one model output field before running the prompt.")

    for index, output_def in enumerate(model_outputs, start=1):
        description = output_def.instructions.strip() or None

        if output_def.field_type == "enum":
            enum_values = enum_values_for_output(config, output_def, enum_values_override)
            enum_cache[output_def.name] = enum_values
            enum_type = make_str_enum(f"EnumField{index}", enum_values)
            annotation = enum_type if output_def.required else enum_type | None
            field_value = Field(... if output_def.required else None, description=description)
        elif output_def.field_type == "text":
            annotation = str if output_def.required else str | None
            field_value = Field(... if output_def.required else None, description=description)
        elif output_def.field_type == "integer":
            annotation = int if output_def.required else int | None
            field_value = Field(... if output_def.required else None, description=description)
        elif output_def.field_type == "boolean":
            annotation = bool if output_def.required else bool | None
            field_value = Field(... if output_def.required else None, description=description)
        elif output_def.field_type == "list[str]":
            if output_def.enum_source_id:
                enum_values = enum_values_for_output(config, output_def, enum_values_override)
                enum_cache[output_def.name] = enum_values
                item_type = make_str_enum(f"EnumListField{index}", enum_values)
                annotation = list[item_type] if output_def.required else list[item_type] | None
            else:
                annotation = list[str] if output_def.required else list[str] | None
            default = ... if output_def.required else None
            field_value = Field(default, min_length=1 if output_def.required else None, description=description)
        else:
            raise ValueError(f"Unsupported output field type: {output_def.field_type}")

        model_fields[output_def.name] = (annotation, field_value)

    response_model = create_model("PromptEditorResponse", __base__=_StructuredResponseModel, **model_fields)
    strict_schema = forbid_additional_props(response_model.model_json_schema())
    return response_model, strict_schema, enum_cache


def _render_source_value(
    rows: list[dict[str, str]],
    column_name: str,
    render_mode: str,
    row_data: dict[str, str] | None,
    constant_value: str | None = None,
) -> str:
    if render_mode == "constant":
        return constant_value or ""
    if render_mode == "row_value":
        if row_data is None:
            return ""
        return str(row_data.get(column_name, ""))

    values = _non_empty_values(rows, column_name)
    if render_mode == "full_column":
        return "\n".join(values)
    if render_mode == "unique_values":
        seen: set[str] = set()
        unique_values: list[str] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                unique_values.append(value)
        return "\n".join(unique_values)
    if render_mode == "joined_text":
        return " ".join(values)
    raise ValueError(f"Unsupported placeholder render mode: {render_mode}")


def render_prompt_text(template_text: str, values: dict[str, str]) -> str:
    def _replace(match: re.Match[str]) -> str:
        token = match.group(1)
        if token not in values:
            raise ValueError(f"Prompt token <{token}> is not bound.")
        return values[token]

    return TOKEN_PATTERN.sub(_replace, template_text)


def resolve_placeholder_values(config: PromptTemplateConfig, row_data: dict[str, str] | None) -> dict[str, str]:
    values: dict[str, str] = {}
    for binding in config.placeholder_bindings:
        if binding.source_kind == "system":
            values[binding.token] = binding.constant_value or ""
            continue

        source = _find_source(config, binding.source_id)
        column_name = binding.column_name or source.selected_column
        if not column_name:
            raise ValueError(f"Placeholder <{binding.token}> is missing a source column.")
        if source.available_columns and column_name not in source.available_columns:
            raise ValueError(
                f"Placeholder <{binding.token}> references unknown column '{column_name}' in '{source.dataset_name}'."
            )

        values[binding.token] = _render_source_value(
            rows=source.rows,
            column_name=column_name,
            render_mode=binding.render_mode if binding.source_kind != "additional" else binding.render_mode or source.render_mode,
            row_data=row_data,
            constant_value=binding.constant_value,
        )

    return values


def render_prompts_for_row(config: PromptTemplateConfig, row_index: int = 0) -> tuple[str, str]:
    hydrated = hydrate_config(config)
    validate_config(hydrated)
    row_data = hydrated.primary_source.rows[row_index]
    placeholder_values = resolve_placeholder_values(hydrated, row_data)
    system_prompt = render_prompt_text(hydrated.system_prompt, placeholder_values) if hydrated.system_prompt else ""
    user_prompt = render_prompt_text(hydrated.user_prompt_template, placeholder_values)

    guidance_lines = [
        f"- {output.name}: {output.instructions.strip()}"
        for output in hydrated.output_definitions
        if output.source_type == "model_output" and output.instructions.strip()
    ]
    if guidance_lines:
        user_prompt = f"{user_prompt}\n\nOutput field instructions:\n" + "\n".join(guidance_lines)
    return system_prompt, user_prompt


def build_request_body(config: PromptTemplateConfig, row_index: int, strict_schema: dict) -> dict[str, Any]:
    system_prompt, user_prompt = render_prompts_for_row(config, row_index)
    body: dict[str, Any] = {
        "model": config.model,
        "input": [],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "PromptEditorResponse",
                "schema": strict_schema,
                "strict": True,
            }
        },
        "metadata": {
            "template_name": config.template_name,
            "row_number": str(row_index + 1),
        },
    }
    if system_prompt:
        body["input"].append({"role": "system", "content": system_prompt})
    body["input"].append({"role": "user", "content": user_prompt})

    if config.advanced.temperature is not None:
        body["temperature"] = config.advanced.temperature
    if config.advanced.max_output_tokens is not None:
        body["max_output_tokens"] = config.advanced.max_output_tokens
    if config.advanced.reasoning_effort:
        body["reasoning"] = {"effort": config.advanced.reasoning_effort}
    if config.advanced.detail_level:
        body["text"]["verbosity"] = config.advanced.detail_level
    return body


def extract_response_text(payload: Any) -> str:
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump(mode="json")
    if isinstance(payload, dict):
        output = payload.get("output", [])
    else:
        output = getattr(payload, "output", [])
    if not output:
        raise ValueError("Model response did not include any output content.")

    first_output = output[0]
    content = first_output.get("content", []) if isinstance(first_output, dict) else getattr(first_output, "content", [])
    if not content:
        raise ValueError("Model response did not include any content blocks.")

    first_content = content[0]
    text = first_content.get("text") if isinstance(first_content, dict) else getattr(first_content, "text", None)
    if text is None:
        raise ValueError("Model response did not include text output.")
    return str(text)


def parse_structured_response(raw_text: str, response_model: type[BaseModel]) -> dict[str, Any]:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model returned invalid JSON: {exc.msg}") from exc

    try:
        parsed = response_model.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Model output did not match the required schema: {exc}") from exc
    return parsed.model_dump(mode="json")


def _coerce_output_value(value: Any, field_type: str) -> Any:
    if value is None:
        return None
    if field_type == "integer":
        return int(value)
    if field_type == "boolean":
        if isinstance(value, bool):
            return value
        lowered = str(value).strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    if field_type == "list[str]" and not isinstance(value, list):
        return [str(value)]
    return value


def build_export_row(
    output_definitions: list[OutputDefinition],
    row_number: int,
    row_data: dict[str, str],
    parsed_output: dict[str, Any] | None,
    raw_response: str,
    error_message: str | None = None,
) -> dict[str, Any]:
    export_row: dict[str, Any] = {
        "row_number": row_number,
        "status": "error" if error_message else "success",
        "error_message": error_message or "",
        "raw_response": raw_response,
    }

    for output in output_definitions:
        if output.source_type == "model_output":
            value = None if parsed_output is None else parsed_output.get(output.name)
        elif output.source_type == "passthrough":
            column_name = output.passthrough_column or output.name
            value = row_data.get(column_name, "")
        elif output.source_type == "system":
            value = output.system_value or ""
        else:
            raise ValueError(f"Unsupported output source type: {output.source_type}")
        export_row[output.name] = _coerce_output_value(value, output.field_type)

    return export_row


def export_rows_to_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.json_normalize(rows, sep=".")
    list_columns = [
        column
        for column in df.columns
        if df[column].apply(lambda value: isinstance(value, Sequence) and not isinstance(value, (str, bytes))).any()
    ]

    for column in list_columns:
        df[column] = df[column].apply(
            lambda value: [None]
            if value is None
            else value
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes))
            else [value]
        )

    if list_columns:
        df = df.explode(list_columns, ignore_index=True)
    return df


def validate_config(config: PromptTemplateConfig) -> None:
    if not config.primary_source.rows:
        raise ValueError("Import a primary source dataset before running the prompt.")
    if not config.primary_source.selected_column:
        raise ValueError("Select a primary source column before running the prompt.")
    if config.primary_source.available_columns and config.primary_source.selected_column not in config.primary_source.available_columns:
        raise ValueError("The selected primary source column is no longer available.")
    if not config.user_prompt_template.strip():
        raise ValueError("Enter a user prompt template before running the prompt.")

    tokens_in_prompts = set(TOKEN_PATTERN.findall(config.system_prompt + "\n" + config.user_prompt_template))
    bindings = {binding.token for binding in config.placeholder_bindings}
    missing = sorted(token for token in tokens_in_prompts if token not in bindings)
    if missing:
        raise ValueError(f"Missing placeholder bindings for: {', '.join(f'<{token}>' for token in missing)}")

    for output in config.output_definitions:
        if output.source_type == "passthrough":
            column_name = output.passthrough_column or output.name
            if column_name not in config.primary_source.passthrough_columns:
                raise ValueError(
                    f"Passthrough output '{output.name}' must reference a column selected in passthrough columns."
                )


def run_live_prompt(config: PromptTemplateConfig, parent=None) -> pd.DataFrame:
    client = get_client()
    hydrated = hydrate_config(config)
    validate_config(hydrated)
    response_model, strict_schema, _ = build_response_model(hydrated)

    rows: list[dict[str, Any]] = []
    total = len(hydrated.primary_source.rows)
    progress = ProgressController.open(parent=parent, total_count=total, title="Processing rows…")
    try:
        for index, row_data in enumerate(hydrated.primary_source.rows, start=1):
            raw_response = ""
            parsed_output: dict[str, Any] | None = None
            error_message: str | None = None
            try:
                request_body = build_request_body(hydrated, index - 1, strict_schema)
                response = client.responses.create(**request_body)
                raw_response = extract_response_text(response)
                parsed_output = parse_structured_response(raw_response, response_model)
            except Exception as exc:
                error_message = str(exc)
            rows.append(
                build_export_row(
                    output_definitions=hydrated.output_definitions,
                    row_number=index,
                    row_data=row_data,
                    parsed_output=parsed_output,
                    raw_response=raw_response,
                    error_message=error_message,
                )
            )
            progress.update(index, message=f"Processed {index} of {total} rows")
    finally:
        progress.close()

    return export_rows_to_dataframe(rows)


def run_single_test_row(config: PromptTemplateConfig) -> dict[str, Any]:
    client = get_client()
    hydrated = hydrate_config(config)
    validate_config(hydrated)
    response_model, strict_schema, _ = build_response_model(hydrated)
    response = client.responses.create(**build_request_body(hydrated, 0, strict_schema))
    raw_response = extract_response_text(response)
    parsed_output = parse_structured_response(raw_response, response_model)
    return build_export_row(
        output_definitions=hydrated.output_definitions,
        row_number=1,
        row_data=hydrated.primary_source.rows[0],
        parsed_output=parsed_output,
        raw_response=raw_response,
    )


def submit_batch_prompt(config: PromptTemplateConfig) -> Any:
    client = get_client()
    hydrated = hydrate_config(config)
    validate_config(hydrated)
    _, strict_schema, enum_cache = build_response_model(hydrated)

    batch_buffer = io.BytesIO()
    batch_buffer.name = "batchinput.jsonl"
    row_contexts: list[BatchRowContext] = []

    for index, row_data in enumerate(hydrated.primary_source.rows, start=1):
        custom_id = f"row-{index:05d}"
        request_body = build_request_body(hydrated, index - 1, strict_schema)
        line = {
            "custom_id": custom_id,
            "method": "POST",
            "url": "/v1/responses",
            "body": request_body,
        }
        batch_buffer.write((json.dumps(line, ensure_ascii=False) + "\n").encode("utf-8"))
        row_contexts.append(BatchRowContext(custom_id=custom_id, row_number=index, row_data=deepcopy(row_data)))

    batch_buffer.seek(0)
    uploaded = client.files.create(file=batch_buffer, purpose="batch")
    batch = client.batches.create(
        input_file_id=uploaded.id,
        endpoint="/v1/responses",
        completion_window="24h",
        metadata={
            "model": hydrated.model,
            "type": hydrated.template_name,
            "dataset(s)": hydrated.primary_source.dataset_name,
        },
    )

    save_batch_job(
        BatchJobRecord(
            batch_id=batch.id,
            project_key=get_project_key(),
            template_name=hydrated.template_name,
            preset_id=hydrated.preset_id,
            model=hydrated.model,
            output_definitions=hydrated.output_definitions,
            row_contexts=row_contexts,
            enum_values_by_output=enum_cache,
        )
    )
    return batch


def load_prompt_editor_batch_results(batch_id: str) -> pd.DataFrame | None:
    record = load_batch_job(batch_id)
    if record is None:
        return None

    client = get_client()
    status = get_batch_status(batch_id)
    if status.output_file_id is None:
        handle_batch_fail(client, status)
        return None

    file_response = client.files.content(status.output_file_id).content
    results = [
        json.loads(line)
        for line in file_response.decode("utf-8").splitlines()
        if line.strip()
    ]

    config = PromptTemplateConfig(
        template_name=record.template_name,
        model=record.model,
        output_definitions=record.output_definitions,
        primary_source=PrimarySourceDefinition(rows=[]),
    )
    response_model, _, _ = build_response_model(config, record.enum_values_by_output)

    row_lookup = {context.custom_id: context for context in record.row_contexts}
    seen_ids: set[str] = set()
    exported_rows: list[dict[str, Any]] = []

    for result in results:
        custom_id = result.get("custom_id", "")
        seen_ids.add(custom_id)
        context = row_lookup.get(custom_id, BatchRowContext(custom_id=custom_id, row_number=0, row_data={}))
        raw_response = ""
        parsed_output: dict[str, Any] | None = None
        error_message: str | None = None
        try:
            body = result["response"]["body"]
            raw_response = extract_response_text(body)
            parsed_output = parse_structured_response(raw_response, response_model)
        except Exception as exc:
            error_message = str(exc)
        exported_rows.append(
            build_export_row(
                output_definitions=record.output_definitions,
                row_number=context.row_number,
                row_data=context.row_data,
                parsed_output=parsed_output,
                raw_response=raw_response,
                error_message=error_message,
            )
        )

    for custom_id, context in row_lookup.items():
        if custom_id in seen_ids:
            continue
        exported_rows.append(
            build_export_row(
                output_definitions=record.output_definitions,
                row_number=context.row_number,
                row_data=context.row_data,
                parsed_output=None,
                raw_response="",
                error_message="No result was returned for this row.",
            )
        )

    exported_rows.sort(key=lambda row: row["row_number"])
    return export_rows_to_dataframe(exported_rows)
