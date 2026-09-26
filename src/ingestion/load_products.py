import csv
import os
import logging

import psycopg
from dotenv import load_dotenv
from decimal import Decimal


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

logger.info("Starting product ingestion")

def validate_product(row):
    required_fields = [
        "product_id",
        "product_name",
        "category",
        "unit_price",
    ]

    for field in required_fields:
        if not row[field].strip():
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
    except Exception:
        raise ValueError(
            f"Invalid unit_price: {row['unit_price']}"
        )

    if unit_price < 0:
        raise ValueError(
            f"unit_price cannot be negative: {unit_price}"
        )

connection = psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)


with open("data/raw/products.csv", newline="") as file:
    reader = csv.DictReader(file)

    try:
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
