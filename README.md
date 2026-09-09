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

## DuckDB Bronze Load

Run `python scripts/load_bronze_duckdb.py` to create `warehouse/fulfillops.duckdb` and load the real Olist CSVs plus generated synthetic operational CSVs into bronze tables. This step preserves the raw CSV field names and does not create silver, gold, or dbt models yet.

## dbt Transform Setup

Run dbt commands from `transform/` with the local profile:

```text
dbt debug --profiles-dir .
```

The dbt project `fulfillops_transform` connects to `../warehouse/fulfillops.duckdb` and defines bronze sources for the real Olist and generated synthetic operational tables. Staging and mart folders are prepared, but silver and gold models are not created yet.

## Day 2 Staging Models

The first dbt staging models live in `transform/models/staging/`. `stg_orders` joins real Olist order and customer fields with synthetic warehouse and carrier assignments, `stg_shipments` calculates delivery and SLA fields, and `stg_issues` standardizes generated issue records. Real late-delivery signals remain separate from synthetic warehouse, carrier, SLA, and issue fields.

Day 2 staging includes dbt tests for uniqueness, relationships, accepted values, and shipment date ordering.

## Day 3 Gold Marts

The first gold marts live in `transform/models/marts/` and include `fct_shipments` plus warehouse, carrier, category, and date dimensions for dashboarding.

Aggregate marts provide dashboard-ready SLA performance by day and quality issue rates by weekly operational segment.

Full Day 3 `dbt build --profiles-dir .` and `dbt docs generate --profiles-dir .` passed from `transform/`.

## Day 4 Anomaly Detection

Run `python scripts/detect_anomalies.py` to score weekly SLA-breach anomalies by warehouse-carrier segment and compare detected weeks against the known injected anomaly labels.

The anomaly workflow now separates SLA-breach drift detection from damaged issue-rate spike detection, then validates each track against the appropriate known injected anomaly.

Headline finding: Carrier B x Southeast FC reached a 30.04% damaged issue rate during the injected spike window versus 0.95% for the same segment outside the spike window.

## Tableau Dashboard Exports

Run `python scripts/export_tableau_datasets.py` to create curated CSV exports in `dashboard/exports/` for Tableau dashboard building.

Tableau Public build instructions are documented in `dashboard/tableau_build_guide.md`.

## Dashboard Screenshots

- [Executive Summary](dashboard/screenshots/executive_summary.png)
- [Ops Drill-down](dashboard/screenshots/ops_drilldown.png)
- [Root-cause Anomaly View](dashboard/screenshots/root_cause_anomaly.png)

## Continuous Integration

GitHub Actions runs Python dependency installation and the committed synthetic config check on push and pull request. Because raw Olist CSVs and DuckDB database files are intentionally not committed, the full local rebuild, dbt build, and anomaly validation steps run in CI only when the Kaggle Olist CSVs are present in `raw/olist/`; full local rebuilds require placing those Kaggle files there first.

## Data Note

Olist data will be used as the real source dataset. Warehouse, carrier, SLA, and issue fields will be synthetic additions created later for the fulfillment operations use case.
