import keyring
from typing import Optional

APP_SERVICE = "CodebookAI"   # shows up as the "service" in the OS vault
ACCOUNT    = "API_KEY"      # the "username" label; you can use per-profile names if needed

def save_api_key(value: str) -> None:
    keyring.set_password(APP_SERVICE, ACCOUNT, value)

def load_api_key() -> Optional[str]:
    return keyring.get_password(APP_SERVICE, ACCOUNT)

def clear_api_key() -> None:
    # Useful for "Sign out" or "Remove key"
    keyring.delete_password(APP_SERVICE, ACCOUNT)
