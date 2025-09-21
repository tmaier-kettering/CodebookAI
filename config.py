"""
DEPRECATED: Legacy configuration file.

This file is deprecated and has been replaced by the secure configuration
system in core.config. Please use the new system which loads configuration
from environment variables.

Migration:
1. Copy .env.example to .env
2. Set your OPENAI_API_KEY in the .env file
3. Update imports to use: from core.config import get_config

Security Note:
API keys should NEVER be hardcoded in source files. They should be loaded
from environment variables or secure configuration files that are not
committed to version control.
"""

import warnings
import os

# Issue deprecation warning
warnings.warn(
    "config.py is deprecated. Use 'from core.config import get_config' instead. "
    "See .env.example for proper configuration setup.",
    DeprecationWarning,
    stacklevel=2
)

# For backward compatibility only - remove this after migration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY environment variable is not set. "
        "Please copy .env.example to .env and set your API key there."
    )