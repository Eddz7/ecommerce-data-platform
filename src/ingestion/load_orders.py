import csv
import os
from datetime import datetime

import psycopg
from dotenv import load_dotenv


load_dotenv()


connection = psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

with open("data/raw/orders.csv", newline="") as file:
    reader = csv.DictReader(file)

    with connection.cursor() as cursor:
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
                """,
                (
                    order_id,
                    customer_id,
                    order_date,
                    row["status"],
                    row["payment_method"],
                ),
            )

connection.commit()
connection.close()

print("Orders inserted successfully!")
