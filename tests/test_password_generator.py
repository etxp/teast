import pytest

from pwvault.password_generator import DIGITS, LOWER, SYMBOLS, UPPER, GeneratorError, generate_password


def test_basic_length():
    pw = generate_password(length=16, digits=2, upper=2, lower=2, symbols=2)
    assert len(pw) == 16


def test_minimum_counts_are_respected():
    pw = generate_password(length=20, digits=3, upper=4, lower=5, symbols=2)
    assert sum(c in DIGITS for c in pw) >= 3
    assert sum(c in UPPER for c in pw) >= 4
    assert sum(c in LOWER for c in pw) >= 5
    assert sum(c in SYMBOLS for c in pw) >= 2
    assert len(pw) == 20


def test_sum_greater_than_length_raises():
    with pytest.raises(GeneratorError):
        generate_password(length=5, digits=3, upper=3, lower=0, symbols=0)


def test_all_zero_raises():
    with pytest.raises(GeneratorError):
        generate_password(length=10, digits=0, upper=0, lower=0, symbols=0)


def test_length_below_one_raises():
    with pytest.raises(GeneratorError):
        generate_password(length=0, digits=1)


def test_exact_sum_equals_length():
    pw = generate_password(length=4, digits=1, upper=1, lower=1, symbols=1)
    assert len(pw) == 4
    assert sum(c in DIGITS for c in pw) >= 1
    assert sum(c in UPPER for c in pw) >= 1
    assert sum(c in LOWER for c in pw) >= 1
    assert sum(c in SYMBOLS for c in pw) >= 1


def test_only_one_type_required():
    pw = generate_password(length=10, digits=0, upper=0, lower=5, symbols=0)
    assert len(pw) == 10
    assert sum(c in LOWER for c in pw) >= 5
    # Remaining chars should all come from the lower-case pool since it's
    # the only pool with a positive minimum.
    assert all(c in LOWER for c in pw)


def test_results_vary_across_calls():
    results = {generate_password(length=16, digits=2, upper=2, lower=2, symbols=2) for _ in range(20)}
    assert len(results) > 1
