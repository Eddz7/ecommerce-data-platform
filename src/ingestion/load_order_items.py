import csv
import logging

import psycopg
from dotenv import load_dotenv
from decimal import Decimal, InvalidOperation
from src.ingestion.validation import validate_columns
from src.ingestion.database import get_connection


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

EXPECTED_COLUMNS = {
    "order_id",
    "product_id",
    "quantity",
    "unit_price",
}

def validate_order_item(row):
    required_fields = [
        "order_id",
        "product_id",
        "quantity",
        "unit_price",
    ]

    for field in required_fields:
        if not row[field].strip():
            raise ValueError(
                f"Missing required field: {field}"
            )
    try:
        int(row["order_id"])
    except ValueError:
        raise ValueError(
            f"Invalid order_id: {row['order_id']}"
        )

    try:
        int(row["product_id"])
    except ValueError:
        raise ValueError(
            f"Invalid product_id: {row['product_id']}"
        )

    try:
        quantity = int(row["quantity"])
    except ValueError:
        raise ValueError(
            f"Invalid quantity: {row['quantity']}"
        )

    if quantity <= 0:
        raise ValueError(
            f"quantity must be greater than zero: {quantity}"
        )

    try:
        unit_price = Decimal(row["unit_price"])
    except InvalidOperation:
        raise ValueError(
            f"Invalid unit_price: {row['unit_price']}"
        )

    if unit_price < 0:
        raise ValueError(
            f"unit_price cannot be negative {unit_price}"
        )

def main():
    logger.info("Starting order_item ingestion")

    connection = get_connection()

    with open("data/raw/order_items.csv", newline="") as file:
        reader = csv.DictReader(file)
        validate_columns(reader.fieldnames, EXPECTED_COLUMNS)

        try:
            with connection.cursor() as cursor:
                records_processed = 0
                records_inserted = 0
                records_skipped = 0
                records_rejected = 0
                for row in reader:
                    records_processed += 1
                    try:
                        validate_order_item(row)
                    except ValueError as error:
                        records_rejected += 1
                        logger.error("Rejected order_item record: %s", error)
                        continue
                    order_id = int(row["order_id"])
                    product_id = int(row["product_id"])
                    quantity = int(row["quantity"])
                    unit_price = Decimal(row["unit_price"])
                    try:
                        cursor.execute(
                            """
                            INSERT INTO order_items (
                                order_id,
                                product_id,
                                quantity,
                                unit_price
                            )
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (order_id, product_id) DO NOTHING
                            """,
                            (
                                order_id,
                                product_id,
                                quantity,
                                unit_price
                            ),
                        )
                    except psycopg.Error:
                        logger.exception(
                            "Database error inserting order item: order_id=%s, product_id=%s",
                            order_id,
                            product_id,
                        )
                        raise

                    if cursor.rowcount == 1:
                        records_inserted += 1
                    else:
                        records_skipped += 1
            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    logger.info(
        "Order items ingestion completed:\n%s records processed\n%s records inserted\n%s records skipped\n%s records rejected",
        records_processed,
        records_inserted,
        records_skipped,
        records_rejected,
    )

if __name__ == "__main__":
    main()
