import csv
import os
from datetime import datetime

import psycopg
from dotenv import load_dotenv
from decimal import Decimal


load_dotenv()


connection = psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)


with open("data/raw/products.csv", newline="") as file:
    reader = csv.DictReader(file)

    with connection.cursor() as cursor:
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
                """,
                (
                    product_id,
                    row["product_name"],
                    row["category"],
                    unit_price,
                ),
            )

connection.commit()
connection.close()

print("Products inserted successfully!")
