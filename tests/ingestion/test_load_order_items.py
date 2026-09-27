import pytest

from src.ingestion import load_order_items
from src.ingestion.load_order_items import validate_order_item


def valid_order_item():
    return {
        "order_id": "1001",
        "product_id": "501",
        "quantity": "2",
        "unit_price": "89.99",
    }


def test_validate_order_item_accepts_valid_record():
    validate_order_item(valid_order_item())


def test_validate_order_item_rejects_missing_required_field():
    row = valid_order_item()
    row["product_id"] = ""

    with pytest.raises(
        ValueError,
        match="Missing required field: product_id",
    ):
        validate_order_item(row)


def test_validate_order_item_rejects_invalid_order_id():
    row = valid_order_item()
    row["order_id"] = "abc"

    with pytest.raises(ValueError, match="Invalid order_id: abc"):
        validate_order_item(row)


def test_validate_order_item_rejects_invalid_product_id():
    row = valid_order_item()
    row["product_id"] = "abc"

    with pytest.raises(ValueError, match="Invalid product_id: abc"):
        validate_order_item(row)


def test_validate_order_item_rejects_invalid_quantity():
    row = valid_order_item()
    row["quantity"] = "abc"

    with pytest.raises(ValueError, match="Invalid quantity: abc"):
        validate_order_item(row)


def test_validate_order_item_rejects_zero_quantity():
    row = valid_order_item()
    row["quantity"] = "0"

    with pytest.raises(
        ValueError,
        match=r"quantity must be greater than zero: 0",
    ):
        validate_order_item(row)


def test_validate_order_item_rejects_negative_quantity():
    row = valid_order_item()
    row["quantity"] = "-1"

    with pytest.raises(
        ValueError,
        match=r"quantity must be greater than zero: -1",
    ):
        validate_order_item(row)


def test_validate_order_item_rejects_invalid_unit_price():
    row = valid_order_item()
    row["unit_price"] = "abc"

    with pytest.raises(ValueError, match="Invalid unit_price: abc"):
        validate_order_item(row)


def test_validate_order_item_rejects_negative_unit_price():
    row = valid_order_item()
    row["unit_price"] = "-10.00"

    with pytest.raises(
        ValueError,
        match=r"unit_price cannot be negative -10\.00",
    ):
        validate_order_item(row)


def test_validate_order_item_rejects_none_field():
    row = valid_order_item()
    row["product_id"] = None

    with pytest.raises(ValueError, match="Missing required field: product_id"):
        validate_order_item(row)


def test_validate_order_item_rejects_whitespace_only_field():
    row = valid_order_item()
    row["product_id"] = "   "

    with pytest.raises(ValueError, match="Missing required field: product_id"):
        validate_order_item(row)


def test_main_closes_connection_when_columns_are_invalid(
    bad_header_csv, fake_connection, monkeypatch
):
    monkeypatch.setattr(load_order_items, "get_connection", lambda: fake_connection)

    with pytest.raises(ValueError, match="Missing required columns"):
        load_order_items.main()

    assert fake_connection.closed
