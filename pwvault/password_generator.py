"""Password generator using a cryptographically secure RNG (secrets).

Rules (per PRD):
  1. digits + upper + lower + symbols <= length, and at least one of the
     four counts must be > 0; otherwise raise GeneratorError.
  2. Place the requested minimum number of characters from each type first.
  3. Fill the remaining slots from the union of every type whose minimum
     count is > 0.
  4. Shuffle the final list with secrets.SystemRandom().shuffle so types
     are not clustered at fixed positions.
"""

import secrets
import string

DIGITS = string.digits
UPPER = string.ascii_uppercase
LOWER = string.ascii_lowercase
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?"


class GeneratorError(Exception):
    """Raised when the requested parameters are invalid."""


def generate_password(length: int, digits: int = 0, upper: int = 0, lower: int = 0, symbols: int = 0) -> str:
    if length < 1:
        raise GeneratorError("長度必須大於等於 1")
    if digits < 0 or upper < 0 or lower < 0 or symbols < 0:
        raise GeneratorError("各類數量不可為負數")

    total_min = digits + upper + lower + symbols
    if total_min == 0:
        raise GeneratorError("至少一種字元類型的數量需大於 0")
    if total_min > length:
        raise GeneratorError("各類數量總和不可超過長度")

    rng = secrets.SystemRandom()
    chars: list[str] = []
    union_pool = ""

    for count, pool in ((digits, DIGITS), (upper, UPPER), (lower, LOWER), (symbols, SYMBOLS)):
        if count > 0:
            chars.extend(secrets.choice(pool) for _ in range(count))
            union_pool += pool

    remaining = length - total_min
    chars.extend(secrets.choice(union_pool) for _ in range(remaining))

    rng.shuffle(chars)
    return "".join(chars)
