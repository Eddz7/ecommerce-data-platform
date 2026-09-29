import pytest

from src.ingestion import load_customers
from src.ingestion.load_customers import validate_customer

NO_EXISTING_EMAILS = {}


def valid_customer():
    return {
        "customer_id": "101",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "country": "USA",
        "signup_date": "2026-01-15",
    }


def test_validate_customer_accepts_valid_record():
    validate_customer(valid_customer(), NO_EXISTING_EMAILS)


def test_validate_customer_rejects_missing_required_field():
    row = valid_customer()
    row["email"] = ""

    with pytest.raises(ValueError, match="Missing required field: email"):
        validate_customer(row, NO_EXISTING_EMAILS)


def test_validate_customer_rejects_invalid_customer_id():
    row = valid_customer()
    row["customer_id"] = "abc"

    with pytest.raises(ValueError, match="Invalid customer_id: abc"):
        validate_customer(row, NO_EXISTING_EMAILS)


def test_validate_customer_rejects_email_belonging_to_another_customer():
    row = valid_customer()
    email_to_customer_id = {row["email"]: 999}

    with pytest.raises(
        ValueError,
        match="Email already belongs to another customer",
    ):
        validate_customer(row, email_to_customer_id)


def test_validate_customer_accepts_email_belonging_to_same_customer():
    row = valid_customer()
    email_to_customer_id = {row["email"]: int(row["customer_id"])}

    validate_customer(row, email_to_customer_id)


def test_validate_customer_rejects_invalid_signup_date():
    row = valid_customer()
    row["signup_date"] = "15-01-2026"

    with pytest.raises(ValueError, match="Invalid signup_date: 15-01-2026"):
        validate_customer(row, NO_EXISTING_EMAILS)


def test_validate_customer_rejects_none_field():
    row = valid_customer()
    row["email"] = None

    with pytest.raises(ValueError, match="Missing required field: email"):
        validate_customer(row, NO_EXISTING_EMAILS)


def test_validate_customer_rejects_whitespace_only_field():
    row = valid_customer()
    row["email"] = "   "

    with pytest.raises(ValueError, match="Missing required field: email"):
        validate_customer(row, NO_EXISTING_EMAILS)


def test_main_closes_connection_when_columns_are_invalid(
    bad_header_csv, fake_connection, monkeypatch
):
    monkeypatch.setattr(load_customers, "get_connection", lambda: fake_connection)

    with pytest.raises(ValueError, match="Missing required columns"):
        load_customers.main()

    assert fake_connection.closed
