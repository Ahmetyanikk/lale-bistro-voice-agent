import pytest

from app.services.codes import confirmation_code_lookup_values, normalize_confirmation_code


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("7K2Q", "7K2Q"),
        ("7k2q", "7K2Q"),
        ("7 K 2 Q", "7K2Q"),
        ("7.k-2 q", "7K2Q"),
        ("LBL-7K2Q", "7K2Q"),
        ("L B L 7 K 2 Q", "7K2Q"),
    ],
)
def test_normalize_confirmation_code_voice_variants(value, expected):
    assert normalize_confirmation_code(value) == expected


def test_confirmation_code_lookup_keeps_legacy_database_compatibility():
    assert confirmation_code_lookup_values("7K2Q") == ("7K2Q", "LBL-7K2Q")
