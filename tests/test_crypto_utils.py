from pwvault import crypto_utils


def test_derive_key_is_deterministic_for_same_salt():
    salt = crypto_utils.generate_salt()
    key1 = crypto_utils.derive_key("hunter2", salt)
    key2 = crypto_utils.derive_key("hunter2", salt)
    assert key1 == key2


def test_derive_key_differs_with_different_salt():
    key1 = crypto_utils.derive_key("hunter2", crypto_utils.generate_salt())
    key2 = crypto_utils.derive_key("hunter2", crypto_utils.generate_salt())
    assert key1 != key2


def test_derive_key_differs_with_different_password():
    salt = crypto_utils.generate_salt()
    key1 = crypto_utils.derive_key("password-a", salt)
    key2 = crypto_utils.derive_key("password-b", salt)
    assert key1 != key2


def test_salt_length():
    salt = crypto_utils.generate_salt()
    assert len(salt) == crypto_utils.SALT_LEN
