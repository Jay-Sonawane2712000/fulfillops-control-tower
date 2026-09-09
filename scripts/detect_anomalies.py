import csv
from pathlib import Path

import duckdb


EXPECTED_ANOMALIES = ("ANOM_SPIKE_001", "ANOM_DRIFT_001")
Z_SCORE_THRESHOLD = 2.0
MIN_SHIPMENTS = 20
MIN_PRIOR_WEEKS = 4


def write_summary(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "anomaly_id",
        "detected",
        "first_detected_week",
        "flagged_segment_weeks",
        "top_flagged_segments",
    ]
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    duckdb_path = project_root / "warehouse" / "fulfillops.duckdb"
    results_path = project_root / "warehouse" / "anomaly_results.csv"
    summary_path = project_root / "warehouse" / "anomaly_validation_summary.csv"

    if not duckdb_path.is_file():
        print(f"FAIL: DuckDB database not found at {duckdb_path.relative_to(project_root)}")
        return 1

    query = f"""
    create or replace temporary table anomaly_results as
    with weekly_segment as (
        select
            time_bucket(interval 1 week, fct.order_purchase_date) as week_start_date,
            fct.warehouse_id,
            warehouse.warehouse_name,
            fct.carrier_id,
            carrier.carrier_name,
            count(*) as shipment_count,
            sum(case when fct.sla_breach_flag then 1 else 0 end) as sla_breach_count,
            cast(sum(case when fct.sla_breach_flag then 1 else 0 end) as double)
                / nullif(count(*), 0) as sla_breach_rate
        from fct_shipments as fct
        left join dim_warehouse as warehouse
            on fct.warehouse_id = warehouse.warehouse_id
        left join dim_carrier as carrier
            on fct.carrier_id = carrier.carrier_id
        group by
            week_start_date,
            fct.warehouse_id,
            warehouse.warehouse_name,
            fct.carrier_id,
            carrier.carrier_name
    ),

    scored as (
        select
            *,
            count(sla_breach_rate) over (
                partition by warehouse_id, carrier_id
                order by week_start_date
                rows between 4 preceding and 1 preceding
            ) as prior_week_count,
            avg(sla_breach_rate) over (
                partition by warehouse_id, carrier_id
                order by week_start_date
                rows between 4 preceding and 1 preceding
            ) as trailing_4_week_mean,
            stddev_samp(sla_breach_rate) over (
                partition by warehouse_id, carrier_id
                order by week_start_date
                rows between 4 preceding and 1 preceding
            ) as trailing_4_week_std
        from weekly_segment
    ),

    labeled as (
        select
            time_bucket(interval 1 week, order_purchase_date) as week_start_date,
            warehouse_id,
            carrier_id,
            string_agg(distinct anomaly_flag, ';' order by anomaly_flag) as known_anomaly_labels
        from fct_shipments
        where anomaly_flag in ('ANOM_SPIKE_001', 'ANOM_DRIFT_001')
        group by
            week_start_date,
            warehouse_id,
            carrier_id
    )

    select
        scored.week_start_date,
        scored.warehouse_id,
        scored.warehouse_name,
        scored.carrier_id,
        scored.carrier_name,
        scored.shipment_count,
        scored.sla_breach_count,
        round(scored.sla_breach_rate, 4) as sla_breach_rate,
        round(scored.trailing_4_week_mean, 4) as trailing_4_week_mean,
        round(scored.trailing_4_week_std, 4) as trailing_4_week_std,
        case
            when scored.prior_week_count >= {MIN_PRIOR_WEEKS}
                and scored.trailing_4_week_std > 0
                then round(
                    (scored.sla_breach_rate - scored.trailing_4_week_mean)
                    / scored.trailing_4_week_std,
                    4
                )
            else null
        end as z_score,
        case
            when scored.shipment_count >= {MIN_SHIPMENTS}
                and scored.prior_week_count >= {MIN_PRIOR_WEEKS}
                and scored.trailing_4_week_std > 0
                and abs(
                    (scored.sla_breach_rate - scored.trailing_4_week_mean)
                    / scored.trailing_4_week_std
                ) >= {Z_SCORE_THRESHOLD}
                then true
            else false
        end as anomaly_detected,
        coalesce(labeled.known_anomaly_labels, 'none') as known_anomaly_labels
    from scored
    left join labeled
        on scored.week_start_date = labeled.week_start_date
        and scored.warehouse_id = labeled.warehouse_id
        and scored.carrier_id = labeled.carrier_id
    order by
        scored.week_start_date,
        scored.warehouse_id,
        scored.carrier_id
    """

    with duckdb.connect(str(duckdb_path)) as connection:
        connection.execute(query)
        connection.execute(
            f"copy anomaly_results to '{results_path.resolve().as_posix()}' "
            "(header, delimiter ',')"
        )

        total_rows = connection.execute("select count(*) from anomaly_results").fetchone()[0]
        flagged_rows = connection.execute(
            "select count(*) from anomaly_results where anomaly_detected"
        ).fetchone()[0]

        summary_rows = []
        for anomaly_id in EXPECTED_ANOMALIES:
            detection = connection.execute(
                """
                select
                    min(week_start_date) filter (where anomaly_detected) as first_detected_week,
                    count(*) filter (where anomaly_detected) as flagged_segment_weeks
                from anomaly_results
                where contains(known_anomaly_labels, ?)
                """,
                [anomaly_id],
            ).fetchone()

            top_segments = connection.execute(
                """
                select
                    warehouse_id || ' x ' || carrier_id || ' (z='
                        || cast(round(z_score, 2) as varchar) || ')' as segment
                from anomaly_results
                where anomaly_detected
                    and contains(known_anomaly_labels, ?)
                order by abs(z_score) desc
                limit 3
                """,
                [anomaly_id],
            ).fetchall()

            first_week = detection[0].isoformat() if detection[0] else ""
            segment_text = "; ".join(row[0] for row in top_segments)
            summary_rows.append(
                {
                    "anomaly_id": anomaly_id,
                    "detected": "yes" if detection[1] > 0 else "no",
                    "first_detected_week": first_week,
                    "flagged_segment_weeks": detection[1],
                    "top_flagged_segments": segment_text,
                }
            )

        write_summary(summary_path, summary_rows)

    print("SLA breach anomaly detection")
    print(f"Database: {duckdb_path.relative_to(project_root)}")
    print(f"Results: {results_path.relative_to(project_root)}")
    print(f"Validation summary: {summary_path.relative_to(project_root)}")
    print(f"Segment-weeks scored: {total_rows}")
    print(f"Flagged segment-weeks: {flagged_rows}")
    print("\nKnown anomaly validation:")
    for row in summary_rows:
        first_week = row["first_detected_week"] or "not detected"
        print(
            f"- {row['anomaly_id']}: detected={row['detected']}, "
            f"first_detected_week={first_week}, "
            f"flagged_segment_weeks={row['flagged_segment_weeks']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
