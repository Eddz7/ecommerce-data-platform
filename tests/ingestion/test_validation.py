import pytest

from src.ingestion.validation import validate_columns


EXPECTED_COLUMNS = {
    "customer_id",
    "first_name",
    "last_name",
    "email",
    "country",
    "signup_date",
}


def test_validate_columns_accepts_expected_columns():
    fieldnames = [
        "customer_id",
        "first_name",
        "last_name",
        "email",
        "country",
        "signup_date",
    ]

    validate_columns(fieldnames, EXPECTED_COLUMNS)


def test_validate_columns_accepts_columns_in_different_order():
    fieldnames = [
        "signup_date",
        "country",
        "email",
        "last_name",
        "customer_id",
        "first_name",
    ]

    validate_columns(fieldnames, EXPECTED_COLUMNS)


def test_validate_columns_rejects_missing_column():
    fieldnames = [
        "customer_id",
        "first_name",
        "last_name",
        "email",
        "country",
    ]

    with pytest.raises(
        ValueError,
        match=r"Missing required columns: \['signup_date'\]",
    ):
        validate_columns(fieldnames, EXPECTED_COLUMNS)


def test_validate_columns_rejects_multiple_missing_columns():
    fieldnames = [
        "customer_id",
        "email",
    ]

    with pytest.raises(
        ValueError,
        match=r"Missing required columns: \['country', 'first_name', 'last_name', 'signup_date'\]",
    ):
        validate_columns(fieldnames, EXPECTED_COLUMNS)


def test_validate_columns_rejects_empty_header():
    with pytest.raises(
        ValueError,
        match=r"Missing required columns: \['country', 'customer_id', 'email', 'first_name', 'last_name', 'signup_date'\]",
    ):
        validate_columns([], EXPECTED_COLUMNS)
