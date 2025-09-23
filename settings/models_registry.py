# models_registry.py
from __future__ import annotations
import json
import threading
from pathlib import Path
from typing import List
from settings import secrets_store
from openai import OpenAI

client = OpenAI(api_key=secrets_store.load_api_key())

# Optional: persist across runs (so you don't hit the API even on first open)
_CACHE_FILE = Path.home() / ".codebookai_models_cache.json"

_LOCK = threading.Lock()
_MODELS: List[str] | None = None

def _load_cache_from_disk() -> list[str] | None:
    try:
        if _CACHE_FILE.exists():
            return json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None

def _save_cache_to_disk(models: list[str]) -> None:
    try:
        _CACHE_FILE.write_text(json.dumps(models), encoding="utf-8")
    except Exception:
        pass

def _fetch_models_from_api() -> list[str]:
    """
    Replace this with your real API call.
    Must return a list[str] of model IDs.
    """
    api_list_of_models = client.models.list()
    models = []
    for m in api_list_of_models.data:
        models.append(m.id)
    return models

def preload_models() -> list[str]:
    """Call this once at app startup (non-UI thread if it might block)."""
    global _MODELS
    with _LOCK:
        if _MODELS is not None:
            return _MODELS

        # Try disk cache first
        cached = _load_cache_from_disk()
        if cached:
            _MODELS = cached
            return _MODELS

        # Fall back to API
        try:
            models = _fetch_models_from_api()
            _MODELS = models
            _save_cache_to_disk(models)
        except Exception:
            # Last-resort fallback list so UI still works
            _MODELS = [
                "gpt-4o", "o3", "gpt-4o-mini", "gpt-5", "gpt-5-mini", "omni-moderate"
            ]
        return _MODELS

def get_models() -> list[str]:
    """
    Returns the cached list. If not preloaded, it loads once lazily.
    Importantly, this does NOT re-hit the API if _MODELS is already set.
    """
    global _MODELS
    with _LOCK:
        if _MODELS is not None:
            return _MODELS
    # Lazy init outside the lock to keep it simple
    return preload_models()

def refresh_models() -> list[str]:
    """
    Optional: force a re-fetch from the API (e.g., behind a 'Refresh' button).
    """
    global _MODELS
    with _LOCK:
        try:
            models = _fetch_models_from_api()
            _MODELS = models
            _save_cache_to_disk(models)
        except Exception:
            # Keep the existing list on failure
            pass
        return _MODELS or []
