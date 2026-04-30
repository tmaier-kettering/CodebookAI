"""
Tests for settings/user_config.py

Covers:
- load_user_settings: returns {} when no file exists, returns data when it does
- save_user_settings: persists data to disk, overwrites on second save
- get_setting: prefers user setting over config default, falls back to
               config attribute, falls back to provided default
- set_setting: persists individual key, does not clobber other keys
- get_user_config_file: returns a path inside get_user_config_dir()
"""

import json
from pathlib import Path

import pytest

from settings.user_config import (
    get_setting,
    get_user_config_dir,
    get_user_config_file,
    load_user_settings,
    save_user_settings,
    set_setting,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def isolated_config_dir(tmp_path, monkeypatch):
    """Redirect all user-config reads/writes to a temp directory."""
    config_dir = tmp_path / "CodebookAI"
    config_dir.mkdir()
    monkeypatch.setattr(
        "settings.user_config.get_user_config_dir", lambda: config_dir
    )
    monkeypatch.setattr(
        "settings.user_config.get_user_config_file",
        lambda: config_dir / "config.json",
    )
    return config_dir


# ---------------------------------------------------------------------------
# load_user_settings
# ---------------------------------------------------------------------------

class TestLoadUserSettings:
    def test_returns_empty_dict_when_no_file(self):
        assert load_user_settings() == {}

    def test_returns_saved_data(self, isolated_config_dir):
        cfg = isolated_config_dir / "config.json"
        cfg.write_text(json.dumps({"model": "gpt-5", "max_batches": 10}))
        result = load_user_settings()
        assert result["model"] == "gpt-5"
        assert result["max_batches"] == 10

    def test_returns_empty_dict_on_invalid_json(self, isolated_config_dir):
        cfg = isolated_config_dir / "config.json"
        cfg.write_text("NOT VALID JSON {{{")
        result = load_user_settings()
        assert result == {}

    def test_returns_empty_dict_on_empty_file(self, isolated_config_dir):
        cfg = isolated_config_dir / "config.json"
        cfg.write_text("")
        result = load_user_settings()
        assert result == {}


# ---------------------------------------------------------------------------
# save_user_settings
# ---------------------------------------------------------------------------

class TestSaveUserSettings:
    def test_roundtrip(self):
        data = {"model": "gpt-4o-mini", "max_batches": 4, "time_zone": "UTC"}
        save_user_settings(data)
        assert load_user_settings() == data

    def test_overwrite_on_second_save(self):
        save_user_settings({"key": "first"})
        save_user_settings({"key": "second"})
        assert load_user_settings()["key"] == "second"

    def test_unicode_values_preserved(self):
        data = {"label": "Ünïcödé — 日本語"}
        save_user_settings(data)
        assert load_user_settings()["label"] == "Ünïcödé — 日本語"

    def test_nested_dict_preserved(self):
        data = {"prefs": {"theme": "dark", "font_size": 14}}
        save_user_settings(data)
        loaded = load_user_settings()
        assert loaded["prefs"]["theme"] == "dark"

    def test_empty_dict_saved(self):
        save_user_settings({})
        assert load_user_settings() == {}


# ---------------------------------------------------------------------------
# get_setting
# ---------------------------------------------------------------------------

class TestGetSetting:
    def test_returns_default_config_attribute(self):
        # 'model' is defined in settings/config.py as 'gpt-4o-mini'
        result = get_setting("model")
        assert result == "gpt-4o-mini"

    def test_user_setting_overrides_config(self):
        save_user_settings({"model": "gpt-5-override"})
        assert get_setting("model") == "gpt-5-override"

    def test_returns_provided_default_when_key_missing(self):
        result = get_setting("nonexistent_key_xyz", default="my_default")
        assert result == "my_default"

    def test_returns_none_when_key_missing_and_no_default(self):
        result = get_setting("nonexistent_key_xyz")
        assert result is None

    def test_user_setting_not_in_config_returned(self):
        save_user_settings({"custom_key": "custom_value"})
        assert get_setting("custom_key") == "custom_value"


# ---------------------------------------------------------------------------
# set_setting
# ---------------------------------------------------------------------------

class TestSetSetting:
    def test_sets_single_key(self):
        set_setting("my_key", "my_value")
        assert get_setting("my_key") == "my_value"

    def test_does_not_clobber_other_keys(self):
        save_user_settings({"key_a": "a", "key_b": "b"})
        set_setting("key_a", "updated")
        assert get_setting("key_b") == "b"

    def test_overwrites_existing_key(self):
        set_setting("x", "first")
        set_setting("x", "second")
        assert get_setting("x") == "second"

    def test_sets_integer_value(self):
        set_setting("max_batches", 99)
        assert get_setting("max_batches") == 99

    def test_sets_boolean_value(self):
        set_setting("feature_flag", True)
        assert get_setting("feature_flag") is True


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

class TestPathHelpers:
    def test_config_file_inside_config_dir(self):
        # Access functions through the module so any monkeypatching applied by
        # the autouse isolated_config_dir fixture is respected for both calls.
        import settings.user_config as uc
        cfg_dir = uc.get_user_config_dir()
        cfg_file = uc.get_user_config_file()
        assert str(cfg_file).startswith(str(cfg_dir))
