import csv
import os
import logging
from datetime import datetime

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
            for row in reader:
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
                records_processed += 1
        connection.commit()
    
    except Exception:
        connection.rollback()
        raise
    
    finally:
        connection.close()

logger.info(
    "Products ingestion completed: %s records processed",
    records_processed,
)
