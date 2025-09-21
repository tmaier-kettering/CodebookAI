"""
Secure configuration management for the Codebook application.

This module provides a robust configuration system that:
- Loads settings from environment variables with fallbacks
- Validates configuration values at startup
- Provides type-safe access to configuration values
- Maintains security by never exposing sensitive values in logs
"""

import os
import logging
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field

from .exceptions import ConfigurationError

# Set up logger for this module
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppConfig:
    """
    Application configuration with secure defaults and validation.
    
    This class holds all configuration values needed by the application.
    Values are loaded from environment variables with sensible defaults.
    
    Attributes:
        openai_api_key: OpenAI API key for authentication
        openai_org_id: Optional OpenAI organization ID
        default_model: Default OpenAI model to use for classification
        batch_completion_window: How long to wait for batch jobs to complete
        batch_description: Description to use for batch jobs
        max_retries: Maximum number of API retry attempts
        request_timeout: Timeout in seconds for API requests
        debug_mode: Whether to enable debug logging
    """
    
    # Core OpenAI configuration
    openai_api_key: str
    openai_org_id: Optional[str] = None
    
    # Model configuration
    default_model: str = "gpt-4-turbo-preview"
    
    # Batch processing configuration
    batch_completion_window: str = "24h"
    batch_description: str = "text_classification"
    
    # API reliability configuration
    max_retries: int = 3
    request_timeout: int = 60
    
    # Development configuration
    debug_mode: bool = False
    
    # Internal configuration (not set by environment)
    _config_loaded: bool = field(default=False, init=False)
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate_config()
        # Mark as loaded to prevent re-validation
        object.__setattr__(self, '_config_loaded', True)
        
    def _validate_config(self) -> None:
        """
        Validate all configuration values.
        
        Raises:
            ConfigurationError: If any configuration value is invalid
        """
        # Validate OpenAI API key format
        if not self.openai_api_key:
            raise ConfigurationError(
                "OpenAI API key is required. Please set OPENAI_API_KEY environment variable.",
                error_code="MISSING_API_KEY"
            )
        
        if not self.openai_api_key.startswith(('sk-', 'sk-proj-')):
            raise ConfigurationError(
                "OpenAI API key format appears invalid. It should start with 'sk-' or 'sk-proj-'.",
                error_code="INVALID_API_KEY_FORMAT"
            )
        
        # Validate batch completion window format
        valid_windows = ['24h', '1h', '2h', '4h', '8h', '12h']
        if self.batch_completion_window not in valid_windows:
            raise ConfigurationError(
                f"Invalid batch completion window '{self.batch_completion_window}'. "
                f"Must be one of: {', '.join(valid_windows)}",
                error_code="INVALID_BATCH_WINDOW"
            )
        
        # Validate retry and timeout values
        if self.max_retries < 0 or self.max_retries > 10:
            raise ConfigurationError(
                f"max_retries must be between 0 and 10, got {self.max_retries}",
                error_code="INVALID_RETRY_COUNT"
            )
            
        if self.request_timeout < 1 or self.request_timeout > 300:
            raise ConfigurationError(
                f"request_timeout must be between 1 and 300 seconds, got {self.request_timeout}",
                error_code="INVALID_TIMEOUT"
            )
    
    @property
    def is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled."""
        return self.debug_mode
    
    def get_openai_client_kwargs(self) -> dict[str, Any]:
        """
        Get keyword arguments for OpenAI client initialization.
        
        Returns:
            Dictionary of arguments to pass to OpenAI client constructor
        """
        kwargs = {
            'api_key': self.openai_api_key,
            'timeout': self.request_timeout,
            'max_retries': self.max_retries,
        }
        
        if self.openai_org_id:
            kwargs['organization'] = self.openai_org_id
            
        return kwargs


def _load_env_file() -> None:
    """
    Load environment variables from .env file if it exists.
    
    This function looks for a .env file in the current directory and loads
    environment variables from it. If python-dotenv is not available,
    it silently continues without loading the file.
    """
    try:
        from dotenv import load_dotenv
        env_file = Path('.env')
        if env_file.exists():
            load_dotenv(env_file)
            logger.debug(f"Loaded environment variables from {env_file}")
    except ImportError:
        logger.debug("python-dotenv not available, skipping .env file loading")


def _get_env_bool(key: str, default: bool = False) -> bool:
    """
    Get a boolean value from environment variables.
    
    Args:
        key: Environment variable name
        default: Default value if not set
        
    Returns:
        Boolean value from environment or default
    """
    value = os.getenv(key, '').lower()
    if value in ('true', '1', 'yes', 'on'):
        return True
    elif value in ('false', '0', 'no', 'off'):
        return False
    else:
        return default


def _get_env_int(key: str, default: int) -> int:
    """
    Get an integer value from environment variables.
    
    Args:
        key: Environment variable name
        default: Default value if not set or invalid
        
    Returns:
        Integer value from environment or default
    """
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        logger.warning(f"Invalid integer value for {key}, using default {default}")
        return default


def get_config() -> AppConfig:
    """
    Load and return application configuration.
    
    This function loads configuration from environment variables with
    secure defaults. It should be called once at application startup.
    
    Returns:
        Configured AppConfig instance
        
    Raises:
        ConfigurationError: If configuration is invalid or incomplete
    """
    # Load .env file if available
    _load_env_file()
    
    # Extract configuration from environment variables
    try:
        config = AppConfig(
            openai_api_key=os.getenv('OPENAI_API_KEY', ''),
            openai_org_id=os.getenv('OPENAI_ORG_ID'),
            default_model=os.getenv('DEFAULT_MODEL', 'gpt-4-turbo-preview'),
            batch_completion_window=os.getenv('BATCH_COMPLETION_WINDOW', '24h'),
            batch_description=os.getenv('BATCH_DESCRIPTION', 'text_classification'),
            max_retries=_get_env_int('MAX_RETRIES', 3),
            request_timeout=_get_env_int('REQUEST_TIMEOUT', 60),
            debug_mode=_get_env_bool('DEBUG', False),
        )
        
        logger.debug("Configuration loaded successfully")
        return config
        
    except Exception as e:
        # Wrap any configuration errors in our custom exception
        if isinstance(e, ConfigurationError):
            raise
        else:
            raise ConfigurationError(
                f"Failed to load configuration: {str(e)}",
                error_code="CONFIG_LOAD_FAILED"
            ) from e


# Global configuration instance (lazy-loaded)
_config_instance: Optional[AppConfig] = None


def get_global_config() -> AppConfig:
    """
    Get the global configuration instance (singleton pattern).
    
    This function ensures that configuration is loaded only once per
    application lifecycle and reused across all modules.
    
    Returns:
        Global AppConfig instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = get_config()
    return _config_instance
