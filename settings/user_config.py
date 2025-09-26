"""
User-specific configuration storage for CodebookAI.

This module handles storing user settings in platform-appropriate directories
instead of writing directly to the application's config.py file. It provides:
- Platform-specific user config directory detection
- JSON-based settings storage in user-writable locations  
- Configuration merging between defaults and user overrides
- Safe fallbacks for bundled environments (PyInstaller, etc.)

User settings are stored in:
- Windows: %APPDATA%/CodebookAI/config.json
- macOS: ~/Library/Application Support/CodebookAI/config.json
- Linux: ~/.config/CodebookAI/config.json
"""

from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import Any, Dict, Optional

from settings import config  # Import for defaults


def get_user_config_dir() -> Path:
    """
    Get the platform-appropriate user configuration directory.
    
    Returns:
        Path to the user configuration directory for CodebookAI
    """
    system = platform.system()
    
    if system == "Windows":
        # Use %APPDATA%/CodebookAI
        appdata = Path.home() / "AppData" / "Roaming"
        # Fallback to environment variable if available
        import os
        if "APPDATA" in os.environ:
            appdata = Path(os.environ["APPDATA"])
        return appdata / "CodebookAI"
    
    elif system == "Darwin":  # macOS
        # Use ~/Library/Application Support/CodebookAI
        return Path.home() / "Library" / "Application Support" / "CodebookAI"
    
    else:  # Linux and other Unix-like systems
        # Use ~/.config/CodebookAI (XDG Base Directory Specification)
        xdg_config = Path.home() / ".config"
        import os
        if "XDG_CONFIG_HOME" in os.environ:
            xdg_config = Path(os.environ["XDG_CONFIG_HOME"])
        return xdg_config / "CodebookAI"


def get_user_config_file() -> Path:
    """
    Get the path to the user configuration JSON file.
    
    Returns:
        Path to config.json in the user config directory
    """
    return get_user_config_dir() / "config.json"


def ensure_user_config_dir() -> Path:
    """
    Ensure the user configuration directory exists.
    
    Returns:
        Path to the user configuration directory
        
    Raises:
        OSError: If directory cannot be created
    """
    config_dir = get_user_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def load_user_settings() -> Dict[str, Any]:
    """
    Load user settings from the JSON config file.
    
    Returns:
        Dictionary of user settings, empty dict if file doesn't exist or is invalid
    """
    try:
        config_file = get_user_config_file()
        if config_file.exists():
            content = config_file.read_text(encoding="utf-8")
            return json.loads(content)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        # Return empty dict on any error - we'll use defaults
        pass
    
    return {}


def save_user_settings(settings: Dict[str, Any]) -> None:
    """
    Save user settings to the JSON config file.
    
    Args:
        settings: Dictionary of settings to save
        
    Raises:
        OSError: If settings cannot be saved
    """
    ensure_user_config_dir()
    config_file = get_user_config_file()
    
    # Write atomically using a temporary file
    temp_file = config_file.with_suffix(".json.tmp")
    content = json.dumps(settings, indent=2, ensure_ascii=False)
    temp_file.write_text(content, encoding="utf-8")
    
    # Atomic replace
    temp_file.replace(config_file)


def get_setting(key: str, default: Any = None) -> Any:
    """
    Get a setting value, preferring user settings over defaults.
    
    Args:
        key: Setting key name
        default: Default value if not found anywhere
        
    Returns:
        Setting value from user config, or from defaults, or provided default
    """
    # First try user settings
    user_settings = load_user_settings()
    if key in user_settings:
        return user_settings[key]
    
    # Then try default config.py
    if hasattr(config, key):
        return getattr(config, key)
    
    # Finally use provided default
    return default


def set_setting(key: str, value: Any) -> None:
    """
    Set a user setting value.
    
    Args:
        key: Setting key name
        value: Setting value to save
        
    Raises:
        OSError: If settings cannot be saved
    """
    user_settings = load_user_settings()
    user_settings[key] = value
    save_user_settings(user_settings)


def get_merged_config() -> Dict[str, Any]:
    """
    Get a merged configuration combining defaults and user overrides.
    
    Returns:
        Dictionary with all configuration values (defaults + user overrides)
    """
    # Start with defaults from config.py
    merged = {}
    
    # Add all attributes from config module (excluding private/special ones)
    for attr_name in dir(config):
        if not attr_name.startswith('_'):
            merged[attr_name] = getattr(config, attr_name)
    
    # Overlay user settings
    user_settings = load_user_settings()
    merged.update(user_settings)
    
    return merged


class ConfigProxy:
    """
    A proxy object that provides attribute access to merged configuration.
    This allows existing code to continue using config.attribute_name syntax.
    """
    
    def __getattr__(self, name: str) -> Any:
        """Get attribute from merged configuration."""
        return get_setting(name)
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Set attribute in user configuration (not allowed in this implementation)."""
        raise AttributeError(f"Direct assignment to config.{name} is not allowed. Use set_setting() instead.")


# Create a proxy instance that can be used to replace the config module
merged_config = ConfigProxy()