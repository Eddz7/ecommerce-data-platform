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

logger.info("Starting order ingestion")


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
            for row in reader:
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
                records_processed += 1
        connection.commit()
    
    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

logger.info(
    "Orders ingestion completed: %s records processed",
    records_processed,
)
