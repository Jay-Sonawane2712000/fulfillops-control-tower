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

## Synthetic Operations Config

The files in `raw/synthetic/` define the planned synthetic operational layer: fulfillment centers, carriers, SLA targets, and known injected anomaly windows. These configs describe the synthetic layer only; order-level synthetic fields will be generated later on top of the real Olist source data.

Known injected anomalies include a Carrier B x Southeast FC damaged-issue spike and a gradual SLA breach drift for one warehouse.

## Generated Synthetic Outputs

Run `python scripts/generate_synthetic_ops.py` after the real Olist CSVs and synthetic config files are present. The script creates order-level synthetic operational files in `raw/synthetic/generated/` for warehouse assignments, carrier assignments, issue flags, and SLA targets. These generated files augment real Olist orders without modifying the raw Olist source CSVs.

## Data Note

Olist data will be used as the real source dataset. Warehouse, carrier, SLA, and issue fields will be synthetic additions created later for the fulfillment operations use case.
