# E-Commerce Data Platform

An end-to-end data engineering project designed to demonstrate modern data engineering concepts and technologies.

## Project Goals

This project will build a complete data platform covering:

- Data ingestion
- Data storage
- Data transformation
- Data modeling
- Data quality
- Workflow orchestration
- Batch and streaming processing
- Cloud infrastructure
- Testing
- CI/CD
- Monitoring
- Analytics

## Technology Stack

The technology stack will evolve throughout the project.

Current technologies:

- Python
- SQL (PostgreSQL, including JSONB and upserts)
- PostgreSQL
- Docker
- Git / GitHub
- pytest (unit tests)

## What's Built So Far

**Batch ingestion into PostgreSQL**

- Four CSV sources (customers, products, orders, order_items) loaded by Python scripts.
- Idempotent reloads: customers, products and orders are upserted, and rows that have not changed are skipped. order_items is append-only, because it records historical transactions.
- Each file loads in a single transaction, and the connection is always closed.

**Data quality**

- Record-level validation: required fields, types, dates, allowed values, and finite non-negative prices.
- Cross-table checks: orders must reference an existing customer, order_items must reference an existing order and product, and an email cannot belong to two customers.
- Rejected records are quarantined in the `rejected_records` table, with the original row stored as JSONB.
- `sql/reports/quality_report.sql` summarizes rejections by table and reason.

See [docs/data-model.md](docs/data-model.md) for the tables and relationships.

## Getting Started

Prerequisites: Python 3.13, Docker, and Git.

```bash
# 1. Create and activate a virtual environment, then install dependencies
python -m venv .venv
source .venv/Scripts/activate      # Git Bash on Windows
pip install -r requirements.txt

# 2. Copy the environment template
cp .env.example .env

# 3. Start PostgreSQL
docker compose up -d

# 4. Create the tables (not applied automatically)
docker exec -i ecommerce-postgres psql -U ecommerce_user -d ecommerce < sql/schema/01_create_tables.sql
docker exec -i ecommerce-postgres psql -U ecommerce_user -d ecommerce < sql/schema/02_create_rejected_records_table.sql

# 5. Run the pipeline (from the repository root)
python -m src.ingestion

# 6. Run the tests
pytest

# 7. View the data quality report
docker exec -i ecommerce-postgres psql -U ecommerce_user -d ecommerce < sql/reports/quality_report.sql
```

## Roadmap

Transformation and analytical modeling, dbt, workflow orchestration, cloud infrastructure, streaming, CI/CD, and monitoring are planned but not yet implemented.
