import csv
import logging
from decimal import Decimal, InvalidOperation

import psycopg
from psycopg.types.json import Jsonb

from src.ingestion.validation import validate_columns
from src.ingestion.database import get_connection

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
        product_id = int(row["product_id"])
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

    if not unit_price.is_finite():
        raise ValueError(
            f"Invalid unit_price: {unit_price}"
        )

    if unit_price < 0:
        raise ValueError(
            f"unit_price cannot be negative: {unit_price}"
        )

    return {
        "product_id": product_id,
        "unit_price": unit_price,
    }


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
                records_updated = 0
                records_skipped = 0
                records_rejected = 0
                for row in reader:
                    records_processed += 1
                    try:
                        parsed = validate_product(row)
                    except ValueError as error:
                        records_rejected += 1
                        logger.error("Rejected product record: %s", error)
                        cursor.execute(
                            """
                            INSERT INTO rejected_records (source_table, raw_data, rejection_reason)
                            VALUES (%s, %s, %s)
                            """,
                            ("products", Jsonb(row), str(error)),
                        )
                        continue
                    product_id = parsed["product_id"]
                    unit_price = parsed["unit_price"]
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
                            ON CONFLICT (product_id) DO UPDATE SET
                                product_name = EXCLUDED.product_name,
                                category = EXCLUDED.category,
                                unit_price = EXCLUDED.unit_price
                            WHERE
                                products.product_name IS DISTINCT FROM EXCLUDED.product_name
                                OR products.category IS DISTINCT FROM EXCLUDED.category
                                OR products.unit_price IS DISTINCT FROM EXCLUDED.unit_price
                            RETURNING (xmax = 0) AS inserted
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
                    result = cursor.fetchone()
                    if result is None:
                        records_skipped += 1
                    elif result[0]:
                        records_inserted += 1
                    else:
                        records_updated += 1
            connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    logger.info(
        "Products ingestion completed:\n%s record(s) processed\n%s record(s) inserted\n%s record(s) updated\n%s record(s) skipped\n%s record(s) rejected",
        records_processed,
        records_inserted,
        records_updated,
        records_skipped,
        records_rejected,
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    main()
