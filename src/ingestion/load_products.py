import csv
import logging

import psycopg
from decimal import Decimal, InvalidOperation
from src.ingestion.validation import validate_columns
from src.ingestion.database import get_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

EXPECTED_COLUMNS = {
    "product_id",
    "product_name",
    "category",
    "unit_price",
}

def validate_product(row):
    required_fields = [
        "product_id",
        "product_name",
        "category",
        "unit_price",
    ]

    for field in required_fields:
        value = row.get(field)
        if value is None or not value.strip():
            raise ValueError(
                f"Missing required field: {field}"
            )

    try:
        int(row["product_id"])
    except ValueError:
        raise ValueError(
            f"Invalid product_id: {row['product_id']}"
        )

    try:
        unit_price = Decimal(row["unit_price"])
    except InvalidOperation:
        raise ValueError(
            f"Invalid unit_price: {row['unit_price']}"
        )

    if unit_price < 0:
        raise ValueError(
            f"unit_price cannot be negative: {unit_price}"
        )


def main():

    logger.info("Starting product ingestion")

    connection = get_connection()

    try:
        with open("data/raw/products.csv", newline="") as file:
            reader = csv.DictReader(file)
            validate_columns(reader.fieldnames, EXPECTED_COLUMNS)

            with connection.cursor() as cursor:
                records_processed = 0
                records_inserted = 0
                records_skipped = 0
                records_rejected = 0
                for row in reader:
                    records_processed += 1
                    try:
                        validate_product(row)
                    except ValueError as error:
                        records_rejected += 1
                        logger.error("Rejected product record: %s", error)
                        continue
                    product_id = int(row["product_id"])
                    unit_price = Decimal(row["unit_price"])
                    try:
                        cursor.execute(
                            """
                            INSERT INTO products (
                                product_id,
                                product_name,
                                category,
                                unit_price
                            )
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (product_id) DO NOTHING
                            """,
                            (
                                product_id,
                                row["product_name"],
                                row["category"],
                                unit_price,
                            ),
                        )
                    except psycopg.Error:
                        logger.exception(
                            "Database error inserting product: product_id=%s",
                            product_id
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
        "Products ingestion completed:\n%s records processed\n%s records inserted\n%s records skipped\n%s records rejected",
        records_processed,
        records_inserted,
        records_skipped,
        records_rejected,
    )

if __name__ == "__main__":
    main()
