from pathlib import Path

import duckdb


OLIST_TABLES = {
    "raw_orders": "olist_orders_dataset.csv",
    "raw_order_items": "olist_order_items_dataset.csv",
    "raw_products": "olist_products_dataset.csv",
    "raw_customers": "olist_customers_dataset.csv",
    "raw_reviews": "olist_order_reviews_dataset.csv",
    "raw_payments": "olist_order_payments_dataset.csv",
    "raw_sellers": "olist_sellers_dataset.csv",
    "raw_geolocation": "olist_geolocation_dataset.csv",
}

SYNTHETIC_TABLES = {
    "raw_warehouse_assignments": "warehouse_assignments.csv",
    "raw_carrier_assignments": "carrier_assignments.csv",
    "raw_sla_targets": "order_sla_targets.csv",
    "raw_issue_flags": "issue_flags.csv",
}


def sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def create_table_from_csv(connection: duckdb.DuckDBPyConnection, table: str, path: Path) -> int:
    if not path.is_file():
        raise FileNotFoundError(f"Missing input CSV for {table}: {path}")

    connection.execute(
        f"""
        CREATE OR REPLACE TABLE {table} AS
        SELECT *
        FROM read_csv_auto('{sql_path(path)}', header = true, sample_size = -1)
        """
    )
    return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    raw_olist_dir = project_root / "raw" / "olist"
    generated_dir = project_root / "raw" / "synthetic" / "generated"
    warehouse_dir = project_root / "warehouse"
    duckdb_path = warehouse_dir / "fulfillops.duckdb"

    warehouse_dir.mkdir(parents=True, exist_ok=True)

    print("DuckDB bronze load")
    print(f"Database: {duckdb_path.relative_to(project_root)}")

    with duckdb.connect(str(duckdb_path)) as connection:
        row_counts = {}

        for table, filename in OLIST_TABLES.items():
            row_counts[table] = create_table_from_csv(
                connection,
                table,
                raw_olist_dir / filename,
            )

        for table, filename in SYNTHETIC_TABLES.items():
            row_counts[table] = create_table_from_csv(
                connection,
                table,
                generated_dir / filename,
            )

    print("\nLoaded bronze tables:")
    for table in sorted(row_counts):
        print(f"- {table}: {row_counts[table]} rows")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
