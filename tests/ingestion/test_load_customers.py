import pytest

from src.ingestion.load_customers import validate_customer


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
    validate_customer(valid_customer())


def test_validate_customer_rejects_missing_required_field():
    row = valid_customer()
    row["email"] = ""

    with pytest.raises(ValueError, match="Missing required field: email"):
        validate_customer(row)


def test_validate_customer_rejects_invalid_customer_id():
    row = valid_customer()
    row["customer_id"] = "abc"

    with pytest.raises(ValueError, match="Invalid customer_id: abc"):
        validate_customer(row)


def test_validate_customer_rejects_invalid_signup_date():
    row = valid_customer()
    row["signup_date"] = "15-01-2026"

    with pytest.raises(ValueError, match="Invalid signup_date: 15-01-2026"):
        validate_customer(row)


def test_validate_customer_rejects_none_field():
    row = valid_customer()
    row["email"] = None

    with pytest.raises(ValueError, match="Missing required field: email"):
        validate_customer(row)

def test_validate_customer_rejects_whitespace_only_field():
    row = valid_customer()
    row["email"] = "   "

    with pytest.raises(ValueError, match="Missing required field: email"):
        validate_customer(row)
