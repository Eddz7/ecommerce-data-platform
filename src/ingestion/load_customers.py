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
            for row in reader:
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
                records_processed += 1
        connection.commit()
    
    except Exception:
        connection.rollback()
        raise
    
    finally:
        connection.close()

logger.info(
    "Customers ingestion completed: %s records processed",
    records_processed,
)
