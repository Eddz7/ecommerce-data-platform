import csv
import os
import logging
from datetime import datetime

import psycopg
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

logger.info("Starting customer ingestion")

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

connection = psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)


with open("data/raw/customers.csv", newline="") as file:
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
                    validate_customer(row)
                except ValueError as error:
                    records_rejected += 1
                    logger.error("Rejected customer record: %s", error)
                    continue
                customer_id = int(row["customer_id"])
                signup_date = datetime.strptime(
                    row["signup_date"],
                    "%Y-%m-%d"
                ).date()

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
    "Customers ingestion completed:\n%s records processed\n%s records inserted\n%s records skipped\n%s records rejected",
    records_processed,
    records_inserted,
    records_skipped,
    records_rejected,
)
