"""
Configuration settings for CodebookAI application.

This module contains non-secret runtime configuration values that control
the application's behavior. Secret values (like API keys) are stored
separately using the keyring system.
"""

# OpenAI model to use for text classification
model = 'o3'

# Maximum number of batch jobs to display in the UI
max_batches = 4

# Default timezone for displaying batch creation times
time_zone = 'US/Eastern'
