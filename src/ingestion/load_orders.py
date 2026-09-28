import csv
import logging
from datetime import datetime

import psycopg

from src.ingestion.validation import validate_columns
from src.ingestion.database import get_connection

logger = logging.getLogger(__name__)


ALLOWED_STATUSES = {"completed", "cancelled"}

ALLOWED_PAYMENT_METHODS = {
    "credit_card",
    "debit_card",
    "paypal",
}

EXPECTED_COLUMNS = {
    "order_id",
    "customer_id",
    "order_date",
    "status",
    "payment_method",
}


def validate_order(row, valid_customer_ids):
    required_fields = [
        "order_id",
        "customer_id",
        "order_date",
        "status",
        "payment_method",
    ]

    for field in required_fields:
        value = row.get(field)
        if value is None or not value.strip():
            raise ValueError(
                f"Missing required field: {field}"
            )

    try:
        order_id = int(row["order_id"])
    except ValueError:
        raise ValueError(
            f"Invalid order_id: {row['order_id']}"
        )

    try:
        customer_id = int(row["customer_id"])
    except ValueError:
        raise ValueError(
            f"Invalid customer_id: {row['customer_id']}"
        )

    if customer_id not in valid_customer_ids:
        raise ValueError(
            f"Customer does not exist: customer_id={customer_id}"
        )

    try:
        order_date = datetime.strptime(
            row["order_date"],
            "%Y-%m-%d"
        ).date()
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

    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "order_date": order_date,
    }


def main():
    logger.info("Starting order ingestion")

    connection = get_connection()

    try:
        with open("data/raw/orders.csv", newline="") as file:
            reader = csv.DictReader(file)
            validate_columns(reader.fieldnames, EXPECTED_COLUMNS)

            with connection.cursor() as cursor:
                cursor.execute("SELECT customer_id FROM customers")
                valid_customer_ids = {record[0] for record in cursor.fetchall()}

                records_processed = 0
                records_inserted = 0
                records_updated = 0
                records_skipped = 0
                records_rejected = 0
                for row in reader:
                    records_processed += 1
                    try:
                        parsed = validate_order(row, valid_customer_ids)
                    except ValueError as error:
                        records_rejected += 1
                        logger.error("Rejected order record: %s", error)
                        continue
                    order_id = parsed["order_id"]
                    customer_id = parsed["customer_id"]
                    order_date = parsed["order_date"]

                    try:
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
                            ON CONFLICT (order_id) DO UPDATE SET
                                customer_id = EXCLUDED.customer_id,
                                order_date = EXCLUDED.order_date,
                                status = EXCLUDED.status,
                                payment_method = EXCLUDED.payment_method
                            WHERE
                                orders.customer_id IS DISTINCT FROM EXCLUDED.customer_id
                                OR orders.order_date IS DISTINCT FROM EXCLUDED.order_date
                                OR orders.status IS DISTINCT FROM EXCLUDED.status
                                OR orders.payment_method IS DISTINCT FROM EXCLUDED.payment_method
                            RETURNING (xmax = 0) AS inserted
                            """,
                            (
                                order_id,
                                customer_id,
                                order_date,
                                row["status"],
                                row["payment_method"],
                            ),
                        )
                    except psycopg.Error:
                        logger.exception(
                            "Database error inserting order: order_id=%s, customer_id=%s",
                            order_id,
                            customer_id,
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
        "Orders ingestion completed:\n%s record(s) processed\n%s record(s) inserted\n%s record(s) updated\n%s record(s) skipped\n%s record(s) rejected",
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
