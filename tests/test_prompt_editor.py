import json

import pytest
from pydantic import ValidationError

from prompt_editor.config import (
    AdditionalSourceDefinition,
    OutputDefinition,
    PlaceholderBinding,
    PrimarySourceDefinition,
    PromptTemplateConfig,
)
from prompt_editor.engine import build_response_model, render_prompts_for_row
from prompt_editor.presets import multi_label_preset, single_label_preset
from prompt_editor.storage import load_template, save_template


@pytest.fixture
def prompt_editor_config_dir(tmp_path, monkeypatch):
    config_root = tmp_path / "config-root"
    config_root.mkdir()
    monkeypatch.setattr("prompt_editor.storage.ensure_user_config_dir", lambda: config_root)
    return config_root


def _base_config() -> PromptTemplateConfig:
    return PromptTemplateConfig(
        template_name="Code quotes",
        system_prompt="Use <labels>.",
        user_prompt_template="Classify <quote> using <labels>.",
        primary_source=PrimarySourceDefinition(
            dataset_name="quotes",
            selected_column="quote",
            available_columns=["quote", "speaker"],
            passthrough_columns=["quote"],
            rows=[{"quote": "A hopeful excerpt", "speaker": "R1"}],
        ),
        additional_sources=[
            AdditionalSourceDefinition(
                source_id="labels",
                dataset_name="labels",
                selected_column="label",
                available_columns=["label"],
                rows=[{"label": "positive"}, {"label": "negative"}, {"label": "positive"}],
            )
        ],
        placeholder_bindings=[
            PlaceholderBinding(token="quote", source_id="primary", source_kind="primary", column_name="quote"),
            PlaceholderBinding(
                token="labels",
                source_id="labels",
                source_kind="additional",
                column_name="label",
                render_mode="unique_values",
            ),
        ],
        output_definitions=[
            OutputDefinition(
                name="label",
                source_type="model_output",
                field_type="enum",
                enum_source_id="labels",
                enum_source_column="label",
            ),
            OutputDefinition(
                name="quote",
                source_type="passthrough",
                field_type="text",
                passthrough_column="quote",
            ),
        ],
    )


class TestPromptTemplatePersistence:
    def test_template_roundtrip_strips_runtime_rows(self, prompt_editor_config_dir):
        config = _base_config()

        save_template(config)

        loaded = load_template("Code quotes")
        assert loaded is not None
        assert loaded.template_name == "Code quotes"
        assert loaded.primary_source.rows == []
        assert loaded.additional_sources[0].rows == []

        raw = json.loads(
            (prompt_editor_config_dir / "prompt_editor").rglob("templates.json").__next__().read_text(encoding="utf-8")
        )
        assert raw[0]["primary_source"]["rows"] == []


class TestPromptRendering:
    def test_placeholder_rendering_uses_unique_values_for_additional_sources(self):
        system_prompt, user_prompt = render_prompts_for_row(_base_config())

        assert "positive\nnegative" in system_prompt
        assert "A hopeful excerpt" in user_prompt
        assert user_prompt.count("positive") == 1


class TestSchemaGeneration:
    def test_multi_label_schema_is_array_of_allowed_enum_values(self):
        config = multi_label_preset()
        config.primary_source.available_columns = ["quote"]
        config.primary_source.selected_column = "quote"
        config.primary_source.rows = [{"quote": "A quote"}]
        config.primary_source.passthrough_columns = ["quote"]
        config.additional_sources[0].available_columns = ["label"]
        config.additional_sources[0].selected_column = "label"
        config.additional_sources[0].rows = [{"label": "a"}, {"label": "b"}]
        config.output_definitions.append(
            OutputDefinition(name="quote", source_type="passthrough", field_type="text", passthrough_column="quote")
        )

        response_model, schema, _ = build_response_model(config)

        response_model.model_validate({"label": ["a", "b"]})
        with pytest.raises(ValidationError):
            response_model.model_validate({"label": ["a", "other"]})
        assert schema["additionalProperties"] is False


class TestStrictSingleLabelBehavior:
    def test_single_label_preset_accepts_only_allowed_values(self):
        config = single_label_preset()
        config.primary_source.available_columns = ["quote"]
        config.primary_source.selected_column = "quote"
        config.primary_source.rows = [{"quote": "A quote"}]
        config.primary_source.passthrough_columns = ["quote"]
        config.additional_sources[0].available_columns = ["label"]
        config.additional_sources[0].selected_column = "label"
        config.additional_sources[0].rows = [{"label": "positive"}, {"label": "negative"}]
        config.output_definitions.append(
            OutputDefinition(name="quote", source_type="passthrough", field_type="text", passthrough_column="quote")
        )

        response_model, _schema, _ = build_response_model(config)

        valid = response_model.model_validate({"label": "positive"})
        assert valid.model_dump()["label"] == "positive"
        with pytest.raises(ValidationError):
            response_model.model_validate({"label": "neutral"})
