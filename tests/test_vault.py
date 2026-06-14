import base64
import json

import pytest

from pwvault import vault


@pytest.fixture(autouse=True)
def isolate_vault_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(vault, "app_dir", lambda: str(tmp_path))
    return tmp_path


def test_vault_exists_lifecycle():
    assert not vault.vault_exists()
    vault.create_vault("master-pass")
    assert vault.vault_exists()


def test_create_and_unlock_vault():
    key, data = vault.create_vault("correct horse battery staple")
    assert data == {"version": 1, "entries": []}

    key2, data2 = vault.unlock_vault("correct horse battery staple")
    assert key2 == key
    assert data2 == data


def test_wrong_password_raises():
    vault.create_vault("right-password")
    with pytest.raises(vault.WrongPasswordError):
        vault.unlock_vault("wrong-password")


def test_vault_file_does_not_contain_plaintext(isolate_vault_dir):
    key, data = vault.create_vault("master-pass")
    data["entries"].append(
        {
            "id": "abc-123",
            "name": "Example Site",
            "username": "alice",
            "password": "SuperSecretPlaintext123",
            "tags": ["work"],
        }
    )
    vault.save_vault(key, data)

    raw = (isolate_vault_dir / vault.VAULT_FILENAME).read_text(encoding="utf-8")
    assert "SuperSecretPlaintext123" not in raw
    assert "Example Site" not in raw
    assert "master-pass" not in raw

    file_data = json.loads(raw)
    assert "kdf" in file_data
    assert "ciphertext" in file_data
    assert base64.b64decode(file_data["kdf"]["salt"])


def test_save_and_reload_roundtrip():
    key, data = vault.create_vault("pw123")
    data["entries"].append(
        {
            "id": "1",
            "name": "Entry A",
            "username": "userA",
            "password": "passA",
            "tags": ["tagA", "tagB"],
        }
    )
    vault.save_vault(key, data)

    key2, data2 = vault.unlock_vault("pw123")
    assert key2 == key
    assert data2["entries"][0]["name"] == "Entry A"
    assert data2["entries"][0]["password"] == "passA"


def test_corrupt_vault_raises():
    vault.create_vault("pw")
    with open(vault.vault_path(), "w", encoding="utf-8") as f:
        f.write("not json")
    with pytest.raises(vault.CorruptVaultError):
        vault.unlock_vault("pw")
