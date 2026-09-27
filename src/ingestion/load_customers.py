import csv
import logging
from datetime import datetime

import psycopg
from src.ingestion.validation import validate_columns
from src.ingestion.database import get_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


EXPECTED_COLUMNS = {
    "customer_id",
    "first_name",
    "last_name",
    "email",
    "country",
    "signup_date",
}


def validate_customer(row):
    required_fields = [
        "customer_id",
        "first_name",
        "last_name",
        "email",
        "country",
        "signup_date",
    ]

    for field in required_fields:
        if not row[field].strip():
            raise ValueError(
                f"Missing required field: {field}"
            )

    try:
        int(row["customer_id"])
    except ValueError:
        raise ValueError(
            f"Invalid customer_id: {row['customer_id']}"
        )

    try:
        datetime.strptime(
            row["signup_date"],
            "%Y-%m-%d"
        )
    except ValueError:
        raise ValueError(
            f"Invalid signup_date: {row['signup_date']}"
        )


def main():
    logger.info("Starting customer ingestion")

    connection = get_connection()

    with open("data/raw/customers.csv", newline="") as file:
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
                        validate_customer(row)
                    except ValueError as error:
                        records_rejected += 1
                        logger.error(
                            "Rejected customer record: %s",
                            error,
                        )
                        continue

                    customer_id = int(row["customer_id"])
                    signup_date = datetime.strptime(
                        row["signup_date"],
                        "%Y-%m-%d"
                    ).date()

                    try:
                        cursor.execute(
                            """
                            INSERT INTO customers (
                                customer_id,
                                first_name,
                                last_name,
                                email,
                                country,
                                signup_date
                            )
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (customer_id) DO NOTHING
                            """,
                            (
                                customer_id,
                                row["first_name"],
                                row["last_name"],
                                row["email"],
                                row["country"],
                                signup_date,
                            ),
                        )
                    except psycopg.Error:
                        logger.exception(
                            "Database error inserting customer: customer_id=%s",
                            customer_id,
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
        "Customers ingestion completed:\n"
        "%s records processed\n"
        "%s records inserted\n"
        "%s records skipped\n"
        "%s records rejected",
        records_processed,
        records_inserted,
        records_skipped,
        records_rejected,
    )


if __name__ == "__main__":
    main()
