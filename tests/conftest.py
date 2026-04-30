"""
Shared pytest configuration, fixtures, and helpers for the CodebookAI test suite.

Sets up:
- The project root on sys.path so tests can import application modules.
- An in-memory keyring backend so tests never touch the OS credential store.
- MPLBACKEND=Agg so matplotlib never tries to open a GUI window.
"""

import os
import sys

# ---------------------------------------------------------------------------
# Environment must be configured BEFORE any project module is imported.
# ---------------------------------------------------------------------------
os.environ.setdefault("MPLBACKEND", "Agg")

# Ensure the project root is importable as top-level packages.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Install an in-memory keyring backend before any project code is imported.
# This prevents tests from touching the OS credential store (GNOME Keyring,
# Windows Credential Manager, etc.) and makes keyring behaviour deterministic.
# ---------------------------------------------------------------------------
import keyring
from keyring.backend import KeyringBackend


class _InMemoryKeyring(KeyringBackend):
    """Thread-safe in-memory keyring used exclusively during tests."""

    priority = 999  # always wins the priority contest

    def __init__(self):
        self._store: dict = {}

    def set_password(self, service: str, username: str, password: str) -> None:
        self._store[(service, username)] = password

    def get_password(self, service: str, username: str):
        return self._store.get((service, username))

    def delete_password(self, service: str, username: str) -> None:
        self._store.pop((service, username), None)


keyring.set_keyring(_InMemoryKeyring())

# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_labels():
    """Return a small list of sentiment labels matching the fixture CSV."""
    return ["positive", "negative", "neutral"]


@pytest.fixture
def sample_quotes():
    """Return a small list of text excerpts for classification tests."""
    return [
        "The product exceeded all of my expectations.",
        "This was a deeply disappointing experience.",
        "The item arrived on time and was as described.",
    ]


@pytest.fixture
def realistic_quotes():
    """A slightly richer set that includes non-ASCII and longer excerpts."""
    return [
        "For the last quarter of 2010, net sales doubled to EUR131m.",
        "All the major construction companies of Finland are operating in Russia.",
        "The Company updates its full year outlook and estimates its results to remain at loss.",
        "Net sales rose by some 14 % year-on-year in the first nine months.",
        "The café déjà vu — naïve résumé — piñata fiancée.",
    ]


@pytest.fixture
def tmp_csv(tmp_path):
    """Return a factory that writes a CSV string to a temp file and returns its path."""

    def _make(content: str, filename: str = "test.csv") -> Path:
        p = tmp_path / filename
        p.write_text(content, encoding="utf-8")
        return p

    return _make
