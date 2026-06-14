"""Encrypted vault file handling.

The vault file (vault.dat) is a JSON document with an unencrypted header
(KDF parameters + salt) and a Fernet-encrypted ciphertext blob. The blob,
once decrypted, is the JSON document described in the PRD:

    {"version": 1, "entries": [...]}
"""

import base64
import json
import os
import sys

from cryptography.fernet import Fernet, InvalidToken

from . import crypto_utils

VAULT_FILENAME = "vault.dat"
DATA_VERSION = 1


class VaultError(Exception):
    """Base class for vault errors."""


class WrongPasswordError(VaultError):
    """Raised when the master password fails to decrypt the vault."""


class CorruptVaultError(VaultError):
    """Raised when the vault file is missing or malformed."""


def app_dir() -> str:
    """Directory the vault file lives in (next to the exe / script)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def vault_path() -> str:
    return os.path.join(app_dir(), VAULT_FILENAME)


def vault_exists() -> bool:
    return os.path.isfile(vault_path())


def _empty_data() -> dict:
    return {"version": DATA_VERSION, "entries": []}


def create_vault(master_password: str) -> tuple[bytes, dict]:
    """Create a brand new vault file protected by master_password.

    Returns (fernet_key, data) for immediate use by the application.
    """
    salt = crypto_utils.generate_salt()
    key = crypto_utils.derive_key(master_password, salt)
    fernet = Fernet(key)

    data = _empty_data()
    ciphertext = fernet.encrypt(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    file_data = {
        "version": DATA_VERSION,
        "kdf": {
            "type": "argon2id",
            "salt": base64.b64encode(salt).decode("ascii"),
            "time_cost": crypto_utils.ARGON2_TIME_COST,
            "memory_cost": crypto_utils.ARGON2_MEMORY_COST,
            "parallelism": crypto_utils.ARGON2_PARALLELISM,
        },
        "ciphertext": ciphertext.decode("ascii"),
    }

    _write_file(file_data)
    return key, data


def unlock_vault(master_password: str) -> tuple[bytes, dict]:
    """Decrypt the existing vault file with master_password.

    Returns (fernet_key, data). Raises WrongPasswordError or
    CorruptVaultError on failure.
    """
    file_data = _read_file()

    try:
        kdf = file_data["kdf"]
        salt = base64.b64decode(kdf["salt"])
        ciphertext = file_data["ciphertext"].encode("ascii")
    except (KeyError, ValueError) as exc:
        raise CorruptVaultError("密碼庫檔案格式錯誤") from exc

    key = crypto_utils.derive_key(
        master_password,
        salt,
        time_cost=kdf.get("time_cost", crypto_utils.ARGON2_TIME_COST),
        memory_cost=kdf.get("memory_cost", crypto_utils.ARGON2_MEMORY_COST),
        parallelism=kdf.get("parallelism", crypto_utils.ARGON2_PARALLELISM),
    )
    fernet = Fernet(key)

    try:
        plaintext = fernet.decrypt(ciphertext)
    except InvalidToken as exc:
        raise WrongPasswordError("主密碼錯誤") from exc

    try:
        data = json.loads(plaintext.decode("utf-8"))
    except ValueError as exc:
        raise CorruptVaultError("密碼庫內容解析失敗") from exc

    return key, data


def save_vault(key: bytes, data: dict) -> None:
    """Re-encrypt data with key and write it back to the vault file."""
    fernet = Fernet(key)
    ciphertext = fernet.encrypt(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    file_data = _read_file()
    file_data["ciphertext"] = ciphertext.decode("ascii")
    file_data["version"] = data.get("version", DATA_VERSION)

    _write_file(file_data)


def _read_file() -> dict:
    try:
        with open(vault_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as exc:
        raise CorruptVaultError("無法讀取密碼庫檔案") from exc


def _write_file(file_data: dict) -> None:
    path = vault_path()
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(file_data, f, ensure_ascii=False)
    os.replace(tmp_path, path)
