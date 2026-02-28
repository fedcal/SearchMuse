"""System keyring integration for secure API key storage.

Uses the ``keyring`` package to store and retrieve LLM provider API keys
from the operating-system credential store (GNOME Keyring, macOS Keychain,
Windows Credential Locker, etc.).

When the ``keyring`` package is not installed the module degrades gracefully:
every public function returns ``None`` or silently does nothing.
"""

from __future__ import annotations

import logging

logger: logging.Logger = logging.getLogger(__name__)

_SERVICE_NAME: str = "searchmuse"

try:
    import keyring as _keyring

    _HAS_KEYRING: bool = True
except ImportError:
    _keyring = None
    _HAS_KEYRING = False


def _make_key(provider: str) -> str:
    """Return the keyring username for *provider*."""
    return f"{_SERVICE_NAME}-{provider}-api-key"


def is_available() -> bool:
    """Return ``True`` when the ``keyring`` package is importable."""
    return _HAS_KEYRING


def get_api_key(provider: str) -> str | None:
    """Retrieve an API key for *provider* from the system keyring.

    Returns ``None`` when the keyring package is absent or when no key
    has been stored for the requested provider.
    """
    if not _HAS_KEYRING:
        return None
    try:
        value: str | None = _keyring.get_password(_SERVICE_NAME, _make_key(provider))
        return value
    except Exception:
        logger.debug("keyring lookup failed for provider=%r", provider, exc_info=True)
        return None


def store_api_key(provider: str, api_key: str) -> bool:
    """Store *api_key* for *provider* in the system keyring.

    Returns ``True`` on success, ``False`` when the keyring package is
    absent or the underlying backend raises.
    """
    if not _HAS_KEYRING:
        return False
    try:
        _keyring.set_password(_SERVICE_NAME, _make_key(provider), api_key)
        return True
    except Exception:
        logger.debug("keyring store failed for provider=%r", provider, exc_info=True)
        return False


def delete_api_key(provider: str) -> bool:
    """Remove the stored API key for *provider*.

    Returns ``True`` on success, ``False`` when the keyring package is
    absent, the key does not exist, or the backend raises.
    """
    if not _HAS_KEYRING:
        return False
    try:
        _keyring.delete_password(_SERVICE_NAME, _make_key(provider))
        return True
    except Exception:
        logger.debug("keyring delete failed for provider=%r", provider, exc_info=True)
        return False
