from __future__ import annotations

import hashlib
import json
from pathlib import Path

from prompt_editor.config import BatchJobRecord, PromptTemplateConfig
from settings.user_config import ensure_user_config_dir


def _project_root(project_root: str | Path | None = None) -> Path:
    return Path(project_root or Path.cwd()).resolve()


def get_project_key(project_root: str | Path | None = None) -> str:
    root = _project_root(project_root)
    digest = hashlib.sha1(str(root).encode("utf-8")).hexdigest()[:12]
    return f"{root.name}-{digest}"


def get_prompt_editor_dir(project_root: str | Path | None = None) -> Path:
    directory = ensure_user_config_dir() / "prompt_editor" / get_project_key(project_root)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_templates_file(project_root: str | Path | None = None) -> Path:
    return get_prompt_editor_dir(project_root) / "templates.json"


def get_batch_jobs_file(project_root: str | Path | None = None) -> Path:
    return get_prompt_editor_dir(project_root) / "batch_jobs.json"


def _load_json(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        pass
    return default


def _save_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_path.replace(path)


def _persistable_template(config: PromptTemplateConfig) -> dict:
    data = config.model_dump(mode="json")
    data["primary_source"]["rows"] = []
    for source in data["additional_sources"]:
        source["rows"] = []
    return data


def list_templates(project_root: str | Path | None = None) -> list[PromptTemplateConfig]:
    raw_templates = _load_json(get_templates_file(project_root), [])
    templates: list[PromptTemplateConfig] = []
    for raw in raw_templates:
        try:
            templates.append(PromptTemplateConfig.model_validate(raw))
        except Exception:
            continue
    return templates


def load_template(template_name: str, project_root: str | Path | None = None) -> PromptTemplateConfig | None:
    for template in list_templates(project_root):
        if template.template_name == template_name:
            return template
    return None


def save_template(config: PromptTemplateConfig, project_root: str | Path | None = None) -> None:
    templates = list_templates(project_root)
    persisted = _persistable_template(config)
    saved = False
    output: list[dict] = []
    for template in templates:
        if template.template_name == config.template_name:
            output.append(persisted)
            saved = True
        else:
            output.append(_persistable_template(template))
    if not saved:
        output.append(persisted)
    output.sort(key=lambda item: item["template_name"].lower())
    _save_json(get_templates_file(project_root), output)


def delete_template(template_name: str, project_root: str | Path | None = None) -> None:
    templates = [t for t in list_templates(project_root) if t.template_name != template_name]
    _save_json(get_templates_file(project_root), [_persistable_template(t) for t in templates])


def save_batch_job(record: BatchJobRecord, project_root: str | Path | None = None) -> None:
    path = get_batch_jobs_file(project_root)
    jobs = _load_json(path, {})
    jobs[record.batch_id] = record.model_dump(mode="json")
    _save_json(path, jobs)


def load_batch_job(batch_id: str, project_root: str | Path | None = None) -> BatchJobRecord | None:
    jobs = _load_json(get_batch_jobs_file(project_root), {})
    raw = jobs.get(batch_id)
    if raw is None:
        return None
    try:
        return BatchJobRecord.model_validate(raw)
    except Exception:
        return None
