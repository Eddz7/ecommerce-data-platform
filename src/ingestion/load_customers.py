import csv
import logging
from datetime import datetime

import psycopg
from psycopg.types.json import Jsonb

from src.ingestion.validation import validate_columns
from src.ingestion.database import get_connection

logger = logging.getLogger(__name__)


EXPECTED_COLUMNS = {
    "customer_id",
    "first_name",
    "last_name",
    "email",
    "country",
    "signup_date",
}


def validate_customer(row, email_to_customer_id):
    required_fields = [
        "customer_id",
        "first_name",
        "last_name",
        "email",
        "country",
        "signup_date",
    ]

    for field in required_fields:
        value = row.get(field)
        if value is None or not value.strip():
            raise ValueError(
                f"Missing required field: {field}"
            )

    try:
        customer_id = int(row["customer_id"])
    except ValueError:
        raise ValueError(
            f"Invalid customer_id: {row['customer_id']}"
        )
    existing_customer_id = email_to_customer_id.get(row["email"])
    if existing_customer_id is not None and existing_customer_id != customer_id:
        raise ValueError(
            f"Email already belongs to another customer: {row['email']}"
        )

    try:
        signup_date = datetime.strptime(
            row["signup_date"],
            "%Y-%m-%d"
        ).date()
    except ValueError:
        raise ValueError(
            f"Invalid signup_date: {row['signup_date']}"
        )

    return {
        "customer_id": customer_id,
        "signup_date": signup_date,
    }


def main():
    logger.info("Starting customer ingestion")

    connection = get_connection()

    try:
        with open("data/raw/customers.csv", newline="") as file:
            reader = csv.DictReader(file)
            validate_columns(reader.fieldnames, EXPECTED_COLUMNS)

            with connection.cursor() as cursor:
                cursor.execute("SELECT customer_id, email FROM customers")
                email_to_customer_id = {email: customer_id for customer_id, email in cursor.fetchall()}

                records_processed = 0
                records_inserted = 0
                records_updated = 0
                records_skipped = 0
                records_rejected = 0

                for row in reader:
                    records_processed += 1

                    try:
                        parsed = validate_customer(row, email_to_customer_id)
                    except ValueError as error:
                        records_rejected += 1
                        logger.error(
                            "Rejected customer record: %s",
                            error,
                        )
                        cursor.execute(
                            """
                            INSERT INTO rejected_records (source_table, raw_data, rejection_reason)
                            VALUES (%s, %s, %s)
                            """,
                            ("customers", Jsonb(row), str(error)),
                        )
                        continue

                    customer_id = parsed["customer_id"]
                    signup_date = parsed["signup_date"]

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
                            ON CONFLICT (customer_id) DO UPDATE SET
                                first_name = EXCLUDED.first_name,
                                last_name = EXCLUDED.last_name,
                                email = EXCLUDED.email,
                                country = EXCLUDED.country,
                                signup_date = EXCLUDED.signup_date
                            WHERE
                                customers.first_name IS DISTINCT FROM EXCLUDED.first_name
                                OR customers.last_name IS DISTINCT FROM EXCLUDED.last_name
                                OR customers.email IS DISTINCT FROM EXCLUDED.email
                                OR customers.country IS DISTINCT FROM EXCLUDED.country
                                OR customers.signup_date IS DISTINCT FROM EXCLUDED.signup_date
                            RETURNING (xmax = 0) AS inserted
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
        "Customers ingestion completed:\n"
        "%s record(s) processed\n"
        "%s record(s) inserted\n"
        "%s record(s) updated\n"
        "%s record(s) skipped\n"
        "%s record(s) rejected",
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
