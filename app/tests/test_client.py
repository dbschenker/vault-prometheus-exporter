import pytest
from unittest.mock import patch
import app.metrics.vault as vault_module


def test_create_client_with_vault_token(monkeypatch):
    """Test that Vault client authenticates using VAULT_TOKEN
    environment variable."""

    monkeypatch.setenv("VAULT_ADDR", "http://127.0.0.1:8200")
    monkeypatch.setenv("VAULT_TOKEN", "test-token")

    with patch.object(vault_module, "VAULT_ADDR", "http://127.0.0.1:8200"):
        with patch('app.metrics.vault.Client') as MockClient:
            MockClient.return_value.is_authenticated.return_value = True
            client = vault_module.create_client()

            MockClient.assert_called_once_with(
                url="http://127.0.0.1:8200",
                token="test-token"
            )
            assert client.is_authenticated()


def test_create_client_with_user_token(monkeypatch, tmp_path):
    """Test that Vault client authenticates using the user token file."""

    token_file = tmp_path / ".vault-token"
    token_file.write_text("user-token-content")

    monkeypatch.setenv("VAULT_ADDR", "http://127.0.0.1:8200")

    with patch.object(vault_module, "VAULT_ADDR", "http://127.0.0.1:8200"):
        with patch.object(vault_module, "VAULT_USER_TOKEN", str(token_file)):
            with patch("app.metrics.vault.Client") as MockClient:
                MockClient.return_value.is_authenticated.return_value = True
                client = vault_module.create_client()

                MockClient.assert_called_once_with(
                    url="http://127.0.0.1:8200",
                    token="user-token-content"
                )
                assert client.is_authenticated()


def test_create_client_no_token(monkeypatch):
    """Test that create_client raises an error if no tokens are available."""

    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    monkeypatch.delenv("VAULT_ADDR", raising=False)
    monkeypatch.setattr("os.path.isfile", lambda path: False)

    with pytest.raises(Exception) as excinfo:
        vault_module.create_client()

    assert "VaultClientConfigError" in str(excinfo.value)
