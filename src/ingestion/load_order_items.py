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
            for row in reader:
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
                records_processed += 1
        connection.commit()
    
    except Exception:
        connection.rollback()
        raise
    
    finally:
        connection.close()

logger.info(
    "Order items ingestion completed: %s records processed",
    records_processed,
)

