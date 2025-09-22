"""
Secure credential storage for CodebookAI using the system keyring.

This module provides a secure way to store and retrieve sensitive credentials
(like API keys) using the operating system's native credential storage.
On Windows this uses Windows Credential Manager, on macOS it uses Keychain,
and on Linux it uses Secret Service API (GNOME Keyring, KDE Wallet, etc.).
"""

import keyring
from typing import Optional

# Service name that appears in the OS credential storage
APP_SERVICE = "CodebookAI"   # shows up as the "service" in the OS vault

# Account identifier for the API key credential
ACCOUNT = "API_KEY"      # the "username" label; you can use per-profile names if needed


def save_api_key(value: str) -> None:
    """
    Store the OpenAI API key securely in the system keyring.
    
    Args:
        value: The API key string to store securely
    """
    keyring.set_password(APP_SERVICE, ACCOUNT, value)


def load_api_key() -> Optional[str]:
    """
    Retrieve the OpenAI API key from the system keyring.
    
    Returns:
        The stored API key string, or None if no key is stored or keyring unavailable
    """
    try:
        return keyring.get_password(APP_SERVICE, ACCOUNT)
    except Exception:
        # Handle cases where keyring is not available (testing environments)
        return None


def clear_api_key() -> None:
    """
    Remove the stored API key from the system keyring.
    
    Useful for "Sign out" or "Remove key" functionality.
    """
    keyring.delete_password(APP_SERVICE, ACCOUNT)
