"""Unit tests for keyring store module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestKeyringStore:
    """Tests for keyring_store with mocked keyring backend."""

    def test_get_api_key_returns_stored_value(self):
        mock_keyring = MagicMock()
        mock_keyring.get_password.return_value = "sk-stored-key"

        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            # Re-import to pick up mock
            import importlib

            from searchmuse.infrastructure import keyring_store

            importlib.reload(keyring_store)

            result = keyring_store.get_api_key("claude")

        assert result == "sk-stored-key"
        mock_keyring.get_password.assert_called_once_with(
            "searchmuse", "searchmuse-claude-api-key",
        )

    def test_get_api_key_returns_none_when_not_found(self):
        mock_keyring = MagicMock()
        mock_keyring.get_password.return_value = None

        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            import importlib

            from searchmuse.infrastructure import keyring_store

            importlib.reload(keyring_store)

            result = keyring_store.get_api_key("openai")

        assert result is None

    def test_store_api_key_returns_true_on_success(self):
        mock_keyring = MagicMock()

        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            import importlib

            from searchmuse.infrastructure import keyring_store

            importlib.reload(keyring_store)

            result = keyring_store.store_api_key("claude", "sk-new-key")

        assert result is True
        mock_keyring.set_password.assert_called_once_with(
            "searchmuse", "searchmuse-claude-api-key", "sk-new-key",
        )

    def test_delete_api_key_returns_true_on_success(self):
        mock_keyring = MagicMock()

        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            import importlib

            from searchmuse.infrastructure import keyring_store

            importlib.reload(keyring_store)

            result = keyring_store.delete_api_key("claude")

        assert result is True
        mock_keyring.delete_password.assert_called_once()

    def test_store_returns_false_on_exception(self):
        mock_keyring = MagicMock()
        mock_keyring.set_password.side_effect = RuntimeError("backend error")

        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            import importlib

            from searchmuse.infrastructure import keyring_store

            importlib.reload(keyring_store)

            result = keyring_store.store_api_key("claude", "key")

        assert result is False

    def test_is_available_returns_true_when_keyring_installed(self):
        mock_keyring = MagicMock()

        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            import importlib

            from searchmuse.infrastructure import keyring_store

            importlib.reload(keyring_store)

            assert keyring_store.is_available() is True
