from pathlib import Path

import duckdb


EXPECTED_TABLES = {
    "raw_orders",
    "raw_order_items",
    "raw_products",
    "raw_customers",
    "raw_reviews",
    "raw_payments",
    "raw_sellers",
    "raw_geolocation",
    "raw_warehouse_assignments",
    "raw_carrier_assignments",
    "raw_sla_targets",
    "raw_issue_flags",
}

SYNTHETIC_TABLES = {
    "raw_warehouse_assignments",
    "raw_carrier_assignments",
    "raw_sla_targets",
    "raw_issue_flags",
}

EXPECTED_SYNTHETIC_ROWS = 32799


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    duckdb_path = project_root / "warehouse" / "fulfillops.duckdb"
    failures = []
    row_counts = {}

    print("DuckDB bronze validation")
    print(f"Database: {duckdb_path.relative_to(project_root)}")

    if not duckdb_path.is_file():
        print("\nFAIL: DuckDB database file does not exist.")
        return 1

    with duckdb.connect(str(duckdb_path), read_only=True) as connection:
        existing_tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'main'
                """
            ).fetchall()
        }

        missing_tables = EXPECTED_TABLES - existing_tables
        if missing_tables:
            failures.append(
                "missing bronze tables: " + ", ".join(sorted(missing_tables))
            )

        for table in sorted(EXPECTED_TABLES & existing_tables):
            row_count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            row_counts[table] = row_count
            if row_count <= 0:
                failures.append(f"{table}: expected more than 0 rows, found {row_count}")

        for table in sorted(SYNTHETIC_TABLES & existing_tables):
            row_count = row_counts[table]
            if row_count != EXPECTED_SYNTHETIC_ROWS:
                failures.append(
                    f"{table}: expected {EXPECTED_SYNTHETIC_ROWS} rows, found {row_count}"
                )

        raw_orders_count = row_counts.get("raw_orders")
        if raw_orders_count is not None and raw_orders_count <= EXPECTED_SYNTHETIC_ROWS:
            failures.append(
                "raw_orders: expected more rows than filtered synthetic outputs, "
                f"found {raw_orders_count}"
            )

    if failures:
        print("\nFAIL: Bronze DuckDB load is not ready.")
        print("\nIssues:")
        for failure in failures:
            print(f"- {failure}")
        if row_counts:
            print("\nTable row counts:")
            for table in sorted(row_counts):
                print(f"- {table}: {row_counts[table]} rows")
        return 1

    print("\nPASS: All expected bronze tables exist with valid row counts.")
    print("\nTable row counts:")
    for table in sorted(row_counts):
        print(f"- {table}: {row_counts[table]} rows")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
