import csv
import os
import logging
from datetime import datetime

import psycopg
from dotenv import load_dotenv


load_dotenv()

ALLOWED_STATUSES = {"completed", "cancelled"}

ALLOWED_PAYMENT_METHODS = {
    "credit_card",
    "debit_card",
    "paypal",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

logger.info("Starting order ingestion")
def validate_order(row):
    required_fields = [
        "order_id",
        "customer_id",
        "order_date",
        "status",
        "payment_method",
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
        int(row["customer_id"])
    except ValueError:
        raise ValueError(
            f"Invalid customer_id: {row['customer_id']}"
        )

    try:
        datetime.strptime(
            row["order_date"],
            "%Y-%m-%d"
        )
    except ValueError:
        raise ValueError(
            f"Invalid order_date: {row['order_date']}"
        )

    if row["status"] not in ALLOWED_STATUSES:
        raise ValueError(
            f"Invalid status: {row['status']}"
        )

    if row["payment_method"] not in ALLOWED_PAYMENT_METHODS:
        raise ValueError(
            f"Invalid payment_method: {row['payment_method']}"
        )


connection = psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

with open("data/raw/orders.csv", newline="") as file:
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
                    validate_order(row)
                except ValueError as error:
                    records_rejected += 1
                    logger.error("Rejected order record: %s", error)
                    continue
                order_id = int(row["order_id"])
                customer_id = int(row["customer_id"])
                order_date = datetime.strptime(
                    row["order_date"],
                    "%Y-%m-%d"
                ).date()

                cursor.execute(
                    """
                    INSERT INTO orders (
                        order_id,
                        customer_id,
                        order_date,
                        status,
                        payment_method
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (order_id) DO NOTHING
                    """,
                    (
                        order_id,
                        customer_id,
                        order_date,
                        row["status"],
                        row["payment_method"],
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
    "Orders ingestion completed:\n%s records processed\n%s records inserted\n%s records skipped\n%s records rejected",
    records_processed,
    records_inserted,
    records_skipped,
    records_rejected,
)
