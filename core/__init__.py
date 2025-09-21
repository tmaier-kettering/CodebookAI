"""
Core module containing configuration, exceptions, and shared utilities.

This module provides the foundational components used throughout the application:
- Configuration management with environment variable support
- Custom exception hierarchy for better error handling
- Shared constants and utilities
"""

from .config import AppConfig, get_config
from .exceptions import (
    CodebookError,
    ConfigurationError,
    ValidationError,
    OpenAIError,
    FileProcessingError
)

__all__ = [
    'AppConfig',
    'get_config',
    'CodebookError',
    'ConfigurationError', 
    'ValidationError',
    'OpenAIError',
    'FileProcessingError'
]
