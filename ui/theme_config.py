"""
Theme configuration and constants for CodebookAI application.

This module provides centralized theme settings, colors, and styling
constants for the CustomTkinter-based UI.
"""

import customtkinter as ctk
from typing import Literal

# Theme mode: "System", "Dark", or "Light"
DEFAULT_THEME_MODE: Literal["System", "Dark", "Light"] = "System"

# Color theme: "blue", "green", "dark-blue"
DEFAULT_COLOR_THEME: Literal["blue", "green", "dark-blue"] = "blue"

# UI Constants
DEFAULT_CORNER_RADIUS = 6
DEFAULT_BORDER_WIDTH = 2
DEFAULT_FONT_SIZE = 13
DEFAULT_TITLE_FONT_SIZE = 16
DEFAULT_HEADER_FONT_SIZE = 20

# Font families
DEFAULT_FONT_FAMILY = "Segoe UI"
MONOSPACE_FONT_FAMILY = "Consolas"

# Spacing constants
PADDING_SMALL = 4
PADDING_MEDIUM = 8
PADDING_LARGE = 16
PADDING_XLARGE = 24

# Widget sizes
BUTTON_WIDTH = 120
ENTRY_WIDTH = 300
SPINBOX_WIDTH = 100

# Window sizing
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600


def initialize_theme(mode: str = DEFAULT_THEME_MODE, color_theme: str = DEFAULT_COLOR_THEME) -> None:
    """
    Initialize the CustomTkinter theme settings.
    
    Args:
        mode: The appearance mode - "System", "Dark", or "Light"
        color_theme: The color theme - "blue", "green", or "dark-blue"
    """
    ctk.set_appearance_mode(mode)
    ctk.set_default_color_theme(color_theme)


def get_font(size: int = DEFAULT_FONT_SIZE, weight: str = "normal") -> tuple:
    """
    Get a font tuple for CustomTkinter widgets.
    
    Args:
        size: Font size in points
        weight: Font weight - "normal" or "bold"
    
    Returns:
        Tuple of (family, size, weight) for CTk font parameter
    """
    return (DEFAULT_FONT_FAMILY, size, weight)


def get_title_font() -> tuple:
    """Get the standard title font."""
    return get_font(DEFAULT_TITLE_FONT_SIZE, "bold")


def get_header_font() -> tuple:
    """Get the standard header font."""
    return get_font(DEFAULT_HEADER_FONT_SIZE, "bold")


def get_monospace_font(size: int = DEFAULT_FONT_SIZE) -> tuple:
    """Get a monospace font for code/data display."""
    return (MONOSPACE_FONT_FAMILY, size, "normal")
