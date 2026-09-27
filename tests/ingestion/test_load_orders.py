import pytest

from src.ingestion.load_orders import validate_order


def valid_order():
    return {
        "order_id": "1001",
        "customer_id": "101",
        "order_date": "2026-01-15",
        "status": "completed",
        "payment_method": "credit_card",
    }


def test_validate_order_accepts_valid_record():
    validate_order(valid_order())


def test_validate_order_rejects_missing_required_field():
    row = valid_order()
    row["status"] = ""

    with pytest.raises(ValueError, match="Missing required field: status"):
        validate_order(row)


def test_validate_order_rejects_invalid_order_id():
    row = valid_order()
    row["order_id"] = "abc"

    with pytest.raises(ValueError, match="Invalid order_id: abc"):
        validate_order(row)


def test_validate_order_rejects_invalid_customer_id():
    row = valid_order()
    row["customer_id"] = "abc"

    with pytest.raises(ValueError, match="Invalid customer_id: abc"):
        validate_order(row)


def test_validate_order_rejects_invalid_order_date():
    row = valid_order()
    row["order_date"] = "15-01-2026"

    with pytest.raises(ValueError, match="Invalid order_date: 15-01-2026"):
        validate_order(row)


def test_validate_order_rejects_invalid_status():
    row = valid_order()
    row["status"] = "pending"

    with pytest.raises(ValueError, match="Invalid status: pending"):
        validate_order(row)


def test_validate_order_rejects_invalid_payment_method():
    row = valid_order()
    row["payment_method"] = "cash"

    with pytest.raises(
        ValueError,
        match="Invalid payment_method: cash",
    ):
        validate_order(row)


def test_validate_order_rejects_none_field():
    row = valid_order()
    row["status"] = None

    with pytest.raises(ValueError, match="Missing required field: status"):
        validate_order(row)


def test_validate_order_rejects_whitespace_only_field():
    row = valid_order()
    row["status"] = "   "

    with pytest.raises(ValueError, match="Missing required field: status"):
        validate_order(row)
