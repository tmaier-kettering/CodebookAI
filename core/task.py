"""
Task engine: the single definition of "prompt + constrained output + column roles"
that replaces the six hardcoded classification/extraction pipelines
(single/multi/keyword x batch/live).

A Task is:
- prompt / system: user-authored text with {column} and {list_name} placeholders.
  Braces = substituted per row (columns) or per task (lists); anything else is
  sent to the model verbatim.
- lists: named constant value sets, each with its own rendering format. A list
  can be dropped into the prompt AND bound to an output field, so the allowed
  values shown to the model and the values it's constrained to are always the
  same list, edited in one place.
- output_fields: the shape of the structured response. This is what used to be
  six separate hardcoded Pydantic models (LabeledQuote, LabeledQuoteMulti,
  KeywordExtraction, and their *_live.py twins) -- now one dynamic model built
  from a list of (name, type) pairs.
- carry_columns: input columns that ride into the output CSV untouched. This is
  independent of the prompt -- a column can be carried without ever being used
  as a {placeholder} (e.g. a pre-existing quote_id).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, create_model

from file_handling.data_conversion import make_str_enum

PLACEHOLDER_RE = re.compile(r"\{([^{}]+)\}")

ListFormat = Literal["comma", "hyphen", "space", "newline"]
FieldType = Literal["choice", "multi_choice", "text_list", "free_text", "number", "yes_no"]

_CHOICE_TYPES = {"choice", "multi_choice"}

DEFAULT_MODEL = "gpt-4o-mini"

# ponytail: name heuristic, not an API capability lookup. Extend if OpenAI adds
# reasoning families -- upgrade to a models_registry capability field if this
# ever needs to be authoritative rather than a best guess.
_REASONING_PREFIXES = ("o1", "o3", "o4", "gpt-5")


def is_reasoning_model(model: str) -> bool:
    """Whether `model` takes `reasoning.effort` instead of `temperature` on the
    Responses API."""
    return model.startswith(_REASONING_PREFIXES)


class TaskValidationError(ValueError):
    """Raised when a Task is internally inconsistent (bad placeholder, dangling
    list reference, etc.) -- always before anything is sent to the API."""


@dataclass
class TaskList:
    """A named, constant value set (e.g. labels) with a prompt rendering format."""
    values: list[str]
    format: ListFormat = "comma"

    def render(self) -> str:
        if self.format == "comma":
            return ", ".join(self.values)
        if self.format == "hyphen":
            return "\n".join(f"- {v}" for v in self.values)
        if self.format == "space":
            return " ".join(self.values)
        if self.format == "newline":
            return "\n".join(self.values)
        raise TaskValidationError(f"Unknown list format: {self.format!r}")

    def to_dict(self) -> dict:
        return {"values": list(self.values), "format": self.format}

    @classmethod
    def from_dict(cls, data: dict) -> "TaskList":
        return cls(values=list(data["values"]), format=data.get("format", "comma"))


@dataclass
class OutputField:
    """One field of the structured output -- one column in the result CSV."""
    name: str
    type: FieldType
    list_ref: str | None = None  # required for choice / multi_choice

    def to_dict(self) -> dict:
        return {"name": self.name, "type": self.type, "list_ref": self.list_ref}

    @classmethod
    def from_dict(cls, data: dict) -> "OutputField":
        return cls(name=data["name"], type=data["type"], list_ref=data.get("list_ref"))


@dataclass
class Task:
    prompt: str
    system: str | None = None
    lists: dict[str, TaskList] = field(default_factory=dict)
    output_fields: list[OutputField] = field(default_factory=list)
    carry_columns: list[str] = field(default_factory=list)
    model: str = DEFAULT_MODEL
    temperature: float | None = None       # standard models only
    reasoning_effort: str | None = None    # "low" | "medium" | "high" -- reasoning models only
    max_output_tokens: int | None = None

    def to_dict(self) -> dict:
        """Serialize for saving as a reusable task file."""
        return {
            "prompt": self.prompt,
            "system": self.system,
            "lists": {name: lst.to_dict() for name, lst in self.lists.items()},
            "output_fields": [f.to_dict() for f in self.output_fields],
            "carry_columns": list(self.carry_columns),
            "model": self.model,
            "temperature": self.temperature,
            "reasoning_effort": self.reasoning_effort,
            "max_output_tokens": self.max_output_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            prompt=data["prompt"],
            system=data.get("system"),
            lists={name: TaskList.from_dict(v) for name, v in data.get("lists", {}).items()},
            output_fields=[OutputField.from_dict(f) for f in data.get("output_fields", [])],
            carry_columns=list(data.get("carry_columns", [])),
            model=data.get("model", DEFAULT_MODEL),
            temperature=data.get("temperature"),
            reasoning_effort=data.get("reasoning_effort"),
            max_output_tokens=data.get("max_output_tokens"),
        )


def build_request_params(task: Task) -> dict:
    """Model + inference params for the Responses API, applying per-model rules
    (the API rejects `temperature` on reasoning models and `reasoning` on
    standard ones)."""
    params: dict = {"model": task.model}
    if is_reasoning_model(task.model):
        if task.reasoning_effort:
            params["reasoning"] = {"effort": task.reasoning_effort}
    elif task.temperature is not None:
        params["temperature"] = task.temperature
    if task.max_output_tokens is not None:
        params["max_output_tokens"] = task.max_output_tokens
    return params


def placeholders_in(text: str | None) -> set[str]:
    """All {name} placeholders referenced in a piece of text."""
    return set(PLACEHOLDER_RE.findall(text or ""))


def validate_task(task: Task, columns: list[str]) -> None:
    """
    Check a task against the set of available input columns. Raises
    TaskValidationError with every problem found (not just the first) so the
    UI can show a complete error list before submission.
    """
    errors: list[str] = []
    known = set(columns) | set(task.lists)

    for ph in placeholders_in(task.prompt) | placeholders_in(task.system):
        if ph not in known:
            errors.append(f"Placeholder {{{ph}}} does not match any input column or list.")

    if not task.output_fields:
        errors.append("Task must define at least one output field.")

    names = [f.name for f in task.output_fields]
    if len(names) != len(set(names)):
        errors.append("Output field names must be unique.")

    for f in task.output_fields:
        if f.type in _CHOICE_TYPES:
            if not f.list_ref:
                errors.append(f"Output field '{f.name}' ({f.type}) must reference a list.")
            elif f.list_ref not in task.lists:
                errors.append(f"Output field '{f.name}' references unknown list '{f.list_ref}'.")

    for col in task.carry_columns:
        if col not in columns:
            errors.append(f"Carried column '{col}' is not in the input data.")

    if errors:
        raise TaskValidationError("\n".join(errors))


def render_prompt(task: Task, row: dict[str, Any], *, text: str | None = None) -> str:
    """
    Substitute {column} (from row) and {list_name} (from task.lists, constant)
    placeholders in `text` (defaults to task.prompt). Used both to build the
    actual request and to power the UI's per-row prompt preview, so preview
    and reality can never diverge.
    """
    src = task.prompt if text is None else text

    def _sub(m: re.Match) -> str:
        key = m.group(1)
        if key in task.lists:
            return task.lists[key].render()
        if key in row:
            return str(row[key])
        raise TaskValidationError(f"Unresolved placeholder: {{{key}}}")

    return PLACEHOLDER_RE.sub(_sub, src)


def build_output_model(task: Task) -> type[BaseModel]:
    """
    Dynamically build one Pydantic model from task.output_fields -- this
    replaces the six hardcoded LabeledQuote/LabeledQuoteMulti/KeywordExtraction
    models. Choice/multi_choice fields become strict string enums bound to the
    referenced list, so the model literally cannot emit an off-list value.
    """
    if not task.output_fields:
        raise TaskValidationError("Task must define at least one output field.")

    annotations: dict[str, tuple] = {}
    for f in task.output_fields:
        if f.type == "choice":
            if f.list_ref not in task.lists:
                raise TaskValidationError(f"Output field '{f.name}' references unknown list '{f.list_ref}'.")
            enum = make_str_enum(f"{f.name}_Choice", task.lists[f.list_ref].values)
            annotations[f.name] = (enum, ...)
        elif f.type == "multi_choice":
            if f.list_ref not in task.lists:
                raise TaskValidationError(f"Output field '{f.name}' references unknown list '{f.list_ref}'.")
            enum = make_str_enum(f"{f.name}_Choice", task.lists[f.list_ref].values)
            annotations[f.name] = (list[enum], Field(..., min_length=1))
        elif f.type == "text_list":
            annotations[f.name] = (list[str], Field(..., min_length=1))
        elif f.type == "free_text":
            annotations[f.name] = (str, ...)
        elif f.type == "number":
            annotations[f.name] = (float, ...)
        elif f.type == "yes_no":
            annotations[f.name] = (bool, ...)
        else:
            raise TaskValidationError(f"Unknown output field type: {f.type!r}")

    return create_model(
        "TaskOutput",
        __config__=ConfigDict(use_enum_values=True, extra="forbid"),
        **annotations,
    )


def forbid_additional_props(schema: dict) -> dict:
    """Recursively set additionalProperties:false on every object schema.
    Required for OpenAI Structured Outputs 'strict' mode."""
    if not isinstance(schema, dict):
        return schema

    if schema.get("type") == "object":
        schema.setdefault("properties", {})
        schema["additionalProperties"] = False
        for prop_schema in schema.get("properties", {}).values():
            forbid_additional_props(prop_schema)
        for prop_schema in schema.get("patternProperties", {}).values():
            forbid_additional_props(prop_schema)

    if schema.get("type") == "array" and "items" in schema:
        forbid_additional_props(schema["items"])

    for key in ("oneOf", "anyOf", "allOf"):
        if key in schema and isinstance(schema[key], list):
            for s in schema[key]:
                forbid_additional_props(s)

    return schema


def build_strict_schema(task: Task) -> dict:
    """The full json_schema payload for the OpenAI 'text.format' request field."""
    return forbid_additional_props(build_output_model(task).model_json_schema())
