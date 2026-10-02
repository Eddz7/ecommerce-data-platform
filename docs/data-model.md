# Data Model

## Source Tables

### customers

**Grain:** One row per customer.

| Column | Description |
|---|---|
| customer_id | Unique customer identifier |
| first_name | Customer first name |
| last_name | Customer last name |
| email | Customer email address |
| country | Customer country |
| signup_date | Date customer registered |

### products

**Grain:** One row per product.

| Column | Description |
|---|---|
| product_id | Unique product identifier |
| product_name | Name of product |
| category | Product category |
| unit_price | Current product price |

### orders

**Grain:** One row per order.

| Column | Description |
|---|---|
| order_id | Unique order identifier |
| customer_id | Customer who placed the order |
| order_date | Date order was placed |
| status | Order status |
| payment_method | Payment method |

### order_items

**Grain:** One row per product within an order.

| Column | Description |
|---|---|
| order_id | Order identifier |
| product_id | Product identifier |
| quantity | Number of units purchased |
| unit_price | Price per unit at time of purchase |

## Data Quality Tables

### rejected_records

**Grain:** One row per rejected ingestion record (an event, not an entity).

| Column | Description |
|---|---|
| id | Surrogate key (auto-incrementing) |
| source_table | Loader the record came from (customers, products, orders, order_items) |
| raw_data | The original CSV row, stored as JSONB |
| rejection_reason | Why the record failed validation |
| rejected_at | When the record was rejected (timezone-aware) |

Rejections are never deduplicated: each rejection is its own event. The table has no foreign keys, because a rejected row may reference things that do not exist, which can be the reason it was rejected.

## Relationships

- One customer can have many orders.
- One order can contain many order items.
- One product can appear in many order items.
- `orders.customer_id` references `customers.customer_id`.
- `order_items.order_id` references `orders.order_id`.
- `order_items.product_id` references `products.product_id`.
