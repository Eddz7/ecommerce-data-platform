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

logger.info("Starting order_item ingestion")

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
    except Exception:
        raise ValueError(
            f"Invalid unit_price: {row['unit_price']}"
        )

    if unit_price < 0:
        raise ValueError(
            f"unit_price cannot be negative {unit_price}"
        )

connection = psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

with open("data/raw/order_items.csv", newline="") as file:
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
                    validate_order_item(row)
                except ValueError as error:
                    records_rejected += 1
                    logger.error("Rejected order_item record: %s", error)
                    continue
                order_id = int(row["order_id"])
                product_id = int(row["product_id"])
                quantity = int(row["quantity"])
                unit_price = Decimal(row["unit_price"])
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
