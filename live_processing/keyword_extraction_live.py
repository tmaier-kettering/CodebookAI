"""Legacy keyword-extraction entry point backed by the prompt editor preset."""

from __future__ import annotations

from typing import Optional
import tkinter as tk

from prompt_editor.presets import KEYWORD_EXTRACTION_PRESET_ID
from prompt_editor.ui import open_prompt_editor


def keyword_extraction_pipeline(parent: Optional[tk.Misc] = None):
    if parent is None:
        return
    open_prompt_editor(parent, preset_id=KEYWORD_EXTRACTION_PRESET_ID, execution_mode="live")
