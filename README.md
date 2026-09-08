# FulfillOps Control Tower

## Problem Statement

FulfillOps Control Tower is a portfolio analytics project for monitoring ecommerce fulfillment performance across orders, warehouses, carriers, SLA status, and operational issues.

## Planned Stack

- Python
- DuckDB
- SQL
- dbt or SQL-based transforms
- Tableau
- Pytest

## Planned Folder Structure

```text
fulfillops-control-tower/
|-- raw/
|   |-- olist/
|   `-- synthetic/
|-- transform/
|-- warehouse/
|-- dashboard/
|-- tests/
|-- docs/
|-- scripts/
|-- .gitignore
|-- README.md
`-- .env.example
```

## Raw Data Setup

Place the real Olist CSV files in `raw/olist/` before running ingestion checks. Synthetic warehouse, carrier, SLA, and issue fields will be generated later and should remain separate from the real Olist source data.

## Data Note

Olist data will be used as the real source dataset. Warehouse, carrier, SLA, and issue fields will be synthetic additions created later for the fulfillment operations use case.
