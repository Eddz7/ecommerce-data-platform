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


with open("data/raw/customers.csv", newline="") as file:
    reader = csv.DictReader(file)

    try:
        with connection.cursor() as cursor:
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
        connection.commit()
    
    except Exception:
        connection.rollback()
        raise
    
    finally:
        connection.close()

print("Customers inserted successfully!")
