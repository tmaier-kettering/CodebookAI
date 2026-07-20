from __future__ import annotations

from prompt_editor.config import (
    AdditionalSourceDefinition,
    OutputDefinition,
    PlaceholderBinding,
    PrimarySourceDefinition,
    PromptTemplateConfig,
)
from settings.user_config import get_setting

SINGLE_LABEL_PRESET_ID = "single-label-classification"
MULTI_LABEL_PRESET_ID = "multi-label-classification"
KEYWORD_EXTRACTION_PRESET_ID = "keyword-extraction"


def _base_template(name: str, preset_id: str) -> PromptTemplateConfig:
    return PromptTemplateConfig(
        template_name=name,
        template_kind="preset",
        preset_id=preset_id,
        model=get_setting("model", "gpt-4o-mini"),
        primary_source=PrimarySourceDefinition(
            dataset_name="quotes",
            selected_column="quote",
        ),
    )


def single_label_preset() -> PromptTemplateConfig:
    return _base_template("Single Label Classification", SINGLE_LABEL_PRESET_ID).model_copy(
        update={
            "system_prompt": "",
            "user_prompt_template": (
                "Label this quote with exactly one label from the allowed set.\n"
                "Allowed labels:\n<labels>\n\n"
                "Quote:\n<quote>"
            ),
            "additional_sources": [
                AdditionalSourceDefinition(
                    source_id="labels",
                    dataset_name="labels",
                    selected_column="label",
                    render_mode="unique_values",
                )
            ],
            "placeholder_bindings": [
                PlaceholderBinding(
                    token="quote",
                    source_id="primary",
                    source_kind="primary",
                    render_mode="row_value",
                ),
                PlaceholderBinding(
                    token="labels",
                    source_id="labels",
                    source_kind="additional",
                    render_mode="unique_values",
                ),
            ],
            "output_definitions": [
                OutputDefinition(
                    name="label",
                    source_type="model_output",
                    field_type="enum",
                    required=True,
                    instructions="Choose exactly one label from the allowed set.",
                    enum_source_id="labels",
                    enum_source_column="label",
                )
            ],
        }
    )


def multi_label_preset() -> PromptTemplateConfig:
    return _base_template("Multi-Label Classification", MULTI_LABEL_PRESET_ID).model_copy(
        update={
            "system_prompt": "",
            "user_prompt_template": (
                "Label this quote using only labels from the allowed set.\n"
                "Return one or more labels when they apply.\n"
                "Allowed labels:\n<labels>\n\n"
                "Quote:\n<quote>"
            ),
            "additional_sources": [
                AdditionalSourceDefinition(
                    source_id="labels",
                    dataset_name="labels",
                    selected_column="label",
                    render_mode="unique_values",
                )
            ],
            "placeholder_bindings": [
                PlaceholderBinding(
                    token="quote",
                    source_id="primary",
                    source_kind="primary",
                    render_mode="row_value",
                ),
                PlaceholderBinding(
                    token="labels",
                    source_id="labels",
                    source_kind="additional",
                    render_mode="unique_values",
                ),
            ],
            "output_definitions": [
                OutputDefinition(
                    name="label",
                    source_type="model_output",
                    field_type="list[str]",
                    required=True,
                    instructions="Return one or more labels from the allowed set only.",
                    enum_source_id="labels",
                    enum_source_column="label",
                )
            ],
        }
    )


def keyword_extraction_preset() -> PromptTemplateConfig:
    return _base_template("Keyword Extraction", KEYWORD_EXTRACTION_PRESET_ID).model_copy(
        update={
            "system_prompt": "You are an expert at structured data extraction.",
            "user_prompt_template": "Extract the keywords from this quote:\n<quote>",
            "placeholder_bindings": [
                PlaceholderBinding(
                    token="quote",
                    source_id="primary",
                    source_kind="primary",
                    render_mode="row_value",
                )
            ],
            "output_definitions": [
                OutputDefinition(
                    name="keywords",
                    source_type="model_output",
                    field_type="list[str]",
                    required=True,
                    instructions="Return a concise list of keywords drawn from the quote.",
                )
            ],
        }
    )


PRESET_FACTORIES = {
    SINGLE_LABEL_PRESET_ID: single_label_preset,
    MULTI_LABEL_PRESET_ID: multi_label_preset,
    KEYWORD_EXTRACTION_PRESET_ID: keyword_extraction_preset,
}


def get_preset(preset_id: str) -> PromptTemplateConfig:
    try:
        return PRESET_FACTORIES[preset_id]()
    except KeyError as exc:
        raise ValueError(f"Unknown prompt editor preset: {preset_id}") from exc


def list_presets() -> list[tuple[str, str]]:
    return [
        (SINGLE_LABEL_PRESET_ID, "Single Label Classification"),
        (MULTI_LABEL_PRESET_ID, "Multi-Label Classification"),
        (KEYWORD_EXTRACTION_PRESET_ID, "Keyword Extraction"),
    ]
