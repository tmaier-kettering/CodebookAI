from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PromptExecutionMode = Literal["live", "batch"]
PromptTemplateKind = Literal["preset", "custom"]
PlaceholderRenderMode = Literal["row_value", "full_column", "unique_values", "joined_text", "constant"]
OutputSourceType = Literal["model_output", "passthrough", "system"]
OutputFieldType = Literal["enum", "text", "integer", "boolean", "list[str]"]

PRIMARY_SOURCE_ID = "primary"
LIVE_ROW_WARNING_THRESHOLD = 50


class PromptEditorBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AdvancedSettings(PromptEditorBaseModel):
    temperature: float | None = None
    max_output_tokens: int | None = None
    reasoning_effort: str | None = None
    detail_level: str | None = None


class PrimarySourceDefinition(PromptEditorBaseModel):
    source_id: str = PRIMARY_SOURCE_ID
    dataset_name: str = ""
    file_path: str | None = None
    has_headers: bool = True
    selected_column: str = ""
    available_columns: list[str] = Field(default_factory=list)
    passthrough_columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, str]] = Field(default_factory=list)


class AdditionalSourceDefinition(PromptEditorBaseModel):
    source_id: str
    dataset_name: str
    file_path: str | None = None
    has_headers: bool = True
    selected_column: str = ""
    available_columns: list[str] = Field(default_factory=list)
    render_mode: PlaceholderRenderMode = "unique_values"
    rows: list[dict[str, str]] = Field(default_factory=list)


class PlaceholderBinding(PromptEditorBaseModel):
    token: str
    source_id: str
    source_kind: Literal["primary", "additional", "system"]
    column_name: str | None = None
    render_mode: PlaceholderRenderMode = "row_value"
    constant_value: str | None = None


class OutputDefinition(PromptEditorBaseModel):
    name: str
    source_type: OutputSourceType
    field_type: OutputFieldType
    required: bool = True
    instructions: str = ""
    enum_source_id: str | None = None
    enum_source_column: str | None = None
    passthrough_column: str | None = None
    system_value: str | None = None


class PromptTemplateConfig(PromptEditorBaseModel):
    version: int = 1
    template_name: str
    template_kind: PromptTemplateKind = "custom"
    preset_id: str | None = None
    execution_mode: PromptExecutionMode = "live"
    model: str = "gpt-4o-mini"
    advanced: AdvancedSettings = Field(default_factory=AdvancedSettings)
    system_prompt: str = ""
    user_prompt_template: str = ""
    primary_source: PrimarySourceDefinition = Field(default_factory=PrimarySourceDefinition)
    additional_sources: list[AdditionalSourceDefinition] = Field(default_factory=list)
    placeholder_bindings: list[PlaceholderBinding] = Field(default_factory=list)
    output_definitions: list[OutputDefinition] = Field(default_factory=list)
    live_row_warning_threshold: int = LIVE_ROW_WARNING_THRESHOLD


class BatchRowContext(PromptEditorBaseModel):
    custom_id: str
    row_number: int
    row_data: dict[str, str] = Field(default_factory=dict)


class BatchJobRecord(PromptEditorBaseModel):
    batch_id: str
    project_key: str
    template_name: str
    preset_id: str | None = None
    model: str
    output_definitions: list[OutputDefinition]
    row_contexts: list[BatchRowContext] = Field(default_factory=list)
    enum_values_by_output: dict[str, list[str]] = Field(default_factory=dict)
