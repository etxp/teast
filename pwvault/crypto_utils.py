"""Key derivation helpers (Argon2id -> Fernet key)."""

import base64
import os

from argon2.low_level import Type, hash_secret_raw

ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536  # KiB (64 MB)
ARGON2_PARALLELISM = 4
ARGON2_HASH_LEN = 32
SALT_LEN = 16


def generate_salt() -> bytes:
    return os.urandom(SALT_LEN)


def derive_key(
    master_password: str,
    salt: bytes,
    time_cost: int = ARGON2_TIME_COST,
    memory_cost: int = ARGON2_MEMORY_COST,
    parallelism: int = ARGON2_PARALLELISM,
) -> bytes:
    """Derive a Fernet-compatible (urlsafe base64) key from the master password."""
    raw = hash_secret_raw(
        secret=master_password.encode("utf-8"),
        salt=salt,
        time_cost=time_cost,
        memory_cost=memory_cost,
        parallelism=parallelism,
        hash_len=ARGON2_HASH_LEN,
        type=Type.ID,
    )
    return base64.urlsafe_b64encode(raw)
