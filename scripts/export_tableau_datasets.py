from pathlib import Path

import duckdb


EXPORTS = {
    "fct_shipments_dashboard.csv": """
        select
            fct.shipment_id,
            fct.order_id,
            fct.order_purchase_date,
            fct.delivered_customer_date,
            fct.estimated_delivery_date,
            fct.warehouse_id,
            warehouse.warehouse_name,
            fct.carrier_id,
            carrier.carrier_name,
            fct.category_name,
            fct.sla_tier,
            fct.actual_delivery_days,
            fct.estimated_delivery_days,
            fct.sla_target_days,
            fct.delay_days,
            fct.sla_breach_flag,
            fct.real_late_delivery_flag,
            fct.issue_type,
            fct.quality_issue_flag,
            fct.anomaly_flag
        from fct_shipments as fct
        left join dim_warehouse as warehouse
            on fct.warehouse_id = warehouse.warehouse_id
        left join dim_carrier as carrier
            on fct.carrier_id = carrier.carrier_id
        order by
            fct.order_purchase_date,
            fct.shipment_id
    """,
    "daily_sla_performance.csv": """
        select
            daily.order_purchase_date,
            daily.warehouse_id,
            warehouse.warehouse_name,
            daily.carrier_id,
            carrier.carrier_name,
            daily.sla_tier,
            daily.shipment_count,
            daily.sla_breach_count,
            daily.on_time_count,
            daily.sla_attainment_pct,
            daily.avg_delay_days,
            daily.real_late_delivery_count
        from agg_daily_sla_performance as daily
        left join dim_warehouse as warehouse
            on daily.warehouse_id = warehouse.warehouse_id
        left join dim_carrier as carrier
            on daily.carrier_id = carrier.carrier_id
        order by
            daily.order_purchase_date,
            daily.warehouse_id,
            daily.carrier_id,
            daily.sla_tier
    """,
    "weekly_quality_by_segment.csv": """
        select
            weekly.week_start_date,
            weekly.warehouse_id,
            warehouse.warehouse_name,
            weekly.carrier_id,
            carrier.carrier_name,
            weekly.category_name,
            weekly.issue_type,
            weekly.shipment_count,
            weekly.issue_count,
            weekly.issue_rate_pct,
            weekly.anomaly_count,
            weekly.dominant_anomaly_flag
        from agg_weekly_quality_by_segment as weekly
        left join dim_warehouse as warehouse
            on weekly.warehouse_id = warehouse.warehouse_id
        left join dim_carrier as carrier
            on weekly.carrier_id = carrier.carrier_id
        order by
            weekly.week_start_date,
            weekly.warehouse_id,
            weekly.carrier_id,
            weekly.category_name,
            weekly.issue_type
    """,
}


def sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def export_query(connection: duckdb.DuckDBPyConnection, output_path: Path, query: str) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    connection.execute(
        f"""
        copy (
            {query}
        ) to '{sql_path(output_path)}' (header, delimiter ',')
        """
    )
    return connection.execute(f"select count(*) from ({query})").fetchone()[0]


def export_anomaly_summary(project_root: Path, exports_dir: Path) -> int:
    source_path = project_root / "warehouse" / "anomaly_validation_summary.csv"
    output_path = exports_dir / "anomaly_summary.csv"
    if not source_path.is_file():
        raise FileNotFoundError(f"Missing anomaly summary input: {source_path}")

    with duckdb.connect() as connection:
        return export_query(
            connection,
            output_path,
            f"select * from read_csv_auto('{sql_path(source_path)}', header = true)",
        )


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    duckdb_path = project_root / "warehouse" / "fulfillops.duckdb"
    exports_dir = project_root / "dashboard" / "exports"

    if not duckdb_path.is_file():
        print(f"FAIL: DuckDB database not found at {duckdb_path.relative_to(project_root)}")
        return 1

    row_counts = {}
    with duckdb.connect(str(duckdb_path), read_only=True) as connection:
        for filename, query in EXPORTS.items():
            row_counts[filename] = export_query(connection, exports_dir / filename, query)

    row_counts["anomaly_summary.csv"] = export_anomaly_summary(project_root, exports_dir)

    print("Tableau dashboard export")
    print(f"Output folder: {exports_dir.relative_to(project_root)}")
    print("\nExported CSV row counts:")
    for filename in sorted(row_counts):
        print(f"- {filename}: {row_counts[filename]} rows")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
