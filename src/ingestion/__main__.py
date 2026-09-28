import logging

from src.ingestion.load_customers import main as load_customers
from src.ingestion.load_products import main as load_products
from src.ingestion.load_orders import main as load_orders
from src.ingestion.load_order_items import main as load_order_items


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    load_customers()
    load_products()
    load_orders()
    load_order_items()


if __name__ == "__main__":
    main()
