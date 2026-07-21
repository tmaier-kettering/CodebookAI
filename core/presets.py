"""
Built-in Task presets reproducing today's three prescriptive tools
(single-label, multi-label, keyword extraction) as starting points for the
Task Builder. Presets are fully editable -- opening one just pre-fills the
builder instead of starting from a blank task.

Every preset expects a "text" column in the imported data. If the user's file
doesn't have a column literally named "text", they rename the {text}
placeholder in the prompt (or their column) -- the builder does no implicit
column mapping.
"""

from __future__ import annotations

from typing import Callable

from core.task import OutputField, Task, TaskList

PresetFactory = tuple[str, Callable[[], Task]]


def single_label_preset() -> Task:
    return Task(
        prompt=(
            "Classify this text using exactly one label from the allowed set.\n"
            "Allowed: {labels}\n"
            "Text: {text}"
        ),
        lists={"labels": TaskList(values=[], format="comma")},
        output_fields=[OutputField(name="label", type="choice", list_ref="labels")],
    )


def multi_label_preset() -> Task:
    return Task(
        prompt=(
            "Label this text with one or more labels from the allowed set only.\n"
            "Allowed: {labels}\n"
            "Text: {text}"
        ),
        lists={"labels": TaskList(values=[], format="comma")},
        output_fields=[OutputField(name="labels", type="multi_choice", list_ref="labels")],
    )


def keyword_extraction_preset() -> Task:
    return Task(
        prompt="Extract the keywords from this text.\nText: {text}",
        system="You are an expert at structured data extraction.",
        output_fields=[OutputField(name="keywords", type="text_list")],
    )


# key -> (display name, factory). Order matters for menu display.
PRESETS: dict[str, PresetFactory] = {
    "single_label": ("Single-Label Classification", single_label_preset),
    "multi_label": ("Multi-Label Classification", multi_label_preset),
    "keyword_extraction": ("Keyword Extraction", keyword_extraction_preset),
}
