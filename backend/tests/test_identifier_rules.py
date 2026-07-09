import pytest

from backend.app.utils.identifier_rules import (
    is_strict_identifier,
    normalize_identifier_for_write,
    resolve_identifier_query,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1", "0001"),
        ("0001", "0001"),
        ("1234", "1234"),
        ("12345", "12345"),
        ("2024W12", "2024W12"),
        (" 7 ", "0007"),
        (" 202606 ", "202606"),
    ],
)
def test_normalize_identifier_for_write(value: str, expected: str) -> None:
    assert normalize_identifier_for_write(value) == expected


@pytest.mark.parametrize("value", ["", "   ", None])
def test_normalize_identifier_for_write_rejects_empty(value: str | None) -> None:
    with pytest.raises(ValueError, match="identifier is required"):
        normalize_identifier_for_write(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1", True),
        ("0001", True),
        ("1234", True),
        ("12345", False),
        ("2024W12", False),
        ("W2401", False),
    ],
)
def test_is_strict_identifier(value: str, expected: bool) -> None:
    assert is_strict_identifier(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1", (["1", "01", "001", "0001"], None)),
        ("0001", (["1", "01", "001", "0001"], None)),
        ("0", (["0", "00", "000", "0000"], None)),
        ("12345", (["12345"], None)),
        ("2024W12", (["2024W12"], None)),
        (" W2401 ", (["W2401"], None)),
        ("", (None, None)),
        ("   ", (None, None)),
        (None, (None, None)),
    ],
)
def test_resolve_identifier_query(value: str | None, expected: tuple[list[str] | None, str | None]) -> None:
    assert resolve_identifier_query(value) == expected
