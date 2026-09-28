import pytest

from src.ingestion import load_products
from src.ingestion.load_products import validate_product


def valid_product():
    return {
        "product_id": "501",
        "product_name": "Wireless Headphones",
        "category": "Electronics",
        "unit_price": "89.99",
    }


def test_validate_product_accepts_valid_record():
    validate_product(valid_product())


def test_validate_product_rejects_missing_required_field():
    row = valid_product()
    row["product_name"] = ""

    with pytest.raises(ValueError, match="Missing required field: product_name"):
        validate_product(row)


def test_validate_product_rejects_invalid_product_id():
    row = valid_product()
    row["product_id"] = "abc"

    with pytest.raises(ValueError, match="Invalid product_id: abc"):
        validate_product(row)


def test_validate_product_rejects_invalid_unit_price():
    row = valid_product()
    row["unit_price"] = "abc"

    with pytest.raises(ValueError, match="Invalid unit_price: abc"):
        validate_product(row)


def test_validate_product_rejects_negative_unit_price():
    row = valid_product()
    row["unit_price"] = "-10.00"

    with pytest.raises(
        ValueError,
        match=r"unit_price cannot be negative: -10\.00",
    ):
        validate_product(row)

def test_validate_product_rejects_nan_unit_price():
    row = valid_product()
    row["unit_price"] = "NaN"

    with pytest.raises(ValueError, match="Invalid unit_price: NaN"):
        validate_product(row)

def test_validate_product_rejects_infinite_unit_price():
    row = valid_product()
    row["unit_price"] = "Infinity"

    with pytest.raises(ValueError, match="Invalid unit_price: Infinity"):
        validate_product(row)

def test_validate_product_rejects_none_field():
    row = valid_product()
    row["product_name"] = None

    with pytest.raises(ValueError, match="Missing required field: product_name"):
        validate_product(row)


def test_validate_product_rejects_whitespace_only_field():
    row = valid_product()
    row["product_name"] = "   "

    with pytest.raises(ValueError, match="Missing required field: product_name"):
        validate_product(row)


def test_main_closes_connection_when_columns_are_invalid(
    bad_header_csv, fake_connection, monkeypatch
):
    monkeypatch.setattr(load_products, "get_connection", lambda: fake_connection)

    with pytest.raises(ValueError, match="Missing required columns"):
        load_products.main()

    assert fake_connection.closed
