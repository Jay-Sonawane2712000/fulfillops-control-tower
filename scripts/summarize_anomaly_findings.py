import csv
from pathlib import Path

import duckdb


SPIKE_ANOMALY_ID = "ANOM_SPIKE_001"
DRIFT_ANOMALY_ID = "ANOM_DRIFT_001"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.2f}%"


def number(value: int | float | None) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    return f"{value:,}"


def write_findings(path: Path, findings: dict[str, object]) -> None:
    content = f"""# Anomaly Findings

## Executive Summary

This Day 4 analysis scored injected synthetic operational anomalies on top of real Olist order records. These are not real Olist business incidents; they are controlled signals generated for the FulfillOps Control Tower portfolio project.

- Total shipments analyzed: {number(findings["total_shipments"])}
- Date range analyzed: {findings["date_start"]} to {findings["date_end"]}
- Total flagged segment-weeks: {number(findings["total_flagged_segment_weeks"])}
- {SPIKE_ANOMALY_ID}: detected={findings["spike_detected"]} by damaged issue-rate detection; first detected week {findings["spike_first_week"]}
- {DRIFT_ANOMALY_ID}: detected={findings["drift_detected"]} by SLA breach-rate detection; first detected week {findings["drift_first_week"]}

## Top Flagged Segments

- Top damaged issue-rate anomaly: {findings["top_damaged_segment"]}
- Top SLA breach-rate anomaly: {findings["top_sla_segment"]}

## {SPIKE_ANOMALY_ID}: Damaged Quality Spike

The injected spike targeted Carrier B x Southeast FC for damaged issues.

- Damaged issue rate during spike window: {pct(findings["spike_damaged_rate"])} ({number(findings["spike_damaged_count"])} damaged issues across {number(findings["spike_shipments"])} shipments)
- Damaged issue rate for the same segment outside the spike window: {pct(findings["outside_spike_damaged_rate"])} ({number(findings["outside_spike_damaged_count"])} damaged issues across {number(findings["outside_spike_shipments"])} shipments)
- Share of damaged issues in the spike window attributable to Carrier B x Southeast FC: {pct(findings["spike_damaged_share"])}

This explains why the original SLA-only detector missed the spike: the injected signal was about quality damage, not delivery lateness.

## {DRIFT_ANOMALY_ID}: SLA Breach Drift

The injected drift targeted {findings["drift_warehouse_name"]}.

- SLA breach rate at the start of the drift window: {pct(findings["drift_start_rate"])} ({number(findings["drift_start_breaches"])} breaches across {number(findings["drift_start_shipments"])} shipments)
- SLA breach rate at the end of the drift window: {pct(findings["drift_end_rate"])} ({number(findings["drift_end_breaches"])} breaches across {number(findings["drift_end_shipments"])} shipments)
- First detected week: {findings["drift_first_week"]}

The start and end rates are nearly flat in the current generated data, so the finding should be framed as a detected synthetic SLA segment anomaly rather than a proven real-world deterioration. The drift detector uses a trailing four-week SLA breach baseline, so detection can appear after the pattern has begun rather than on the first affected day.
"""
    path.write_text(content, encoding="utf-8")


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    duckdb_path = project_root / "warehouse" / "fulfillops.duckdb"
    results_path = project_root / "warehouse" / "anomaly_results.csv"
    summary_path = project_root / "warehouse" / "anomaly_validation_summary.csv"
    anomaly_windows_path = project_root / "raw" / "synthetic" / "anomaly_windows.csv"
    findings_path = project_root / "docs" / "anomaly_findings.md"

    required_paths = [duckdb_path, results_path, summary_path, anomaly_windows_path]
    missing_paths = [path for path in required_paths if not path.is_file()]
    if missing_paths:
        print("FAIL: Missing required inputs.")
        for path in missing_paths:
            print(f"- {path.relative_to(project_root)}")
        return 1

    validation_rows = {
        row["anomaly_id"]: row for row in read_csv_rows(summary_path)
    }
    windows = {row["anomaly_id"]: row for row in read_csv_rows(anomaly_windows_path)}

    spike_window = windows[SPIKE_ANOMALY_ID]
    drift_window = windows[DRIFT_ANOMALY_ID]

    with duckdb.connect(str(duckdb_path), read_only=True) as connection:
        total_shipments, date_start, date_end = connection.execute(
            """
            select count(*), min(order_purchase_date), max(order_purchase_date)
            from fct_shipments
            """
        ).fetchone()

        total_flagged_segment_weeks = connection.execute(
            """
            select count(*)
            from read_csv_auto(?, header = true)
            where anomaly_detected
            """,
            [str(results_path)],
        ).fetchone()[0]

        top_damaged = connection.execute(
            """
            select warehouse_name, carrier_name, week_start_date, damaged_issue_rate, z_score
            from read_csv_auto(?, header = true)
            where detection_metric = 'damaged_issue_rate'
                and anomaly_detected
            order by abs(z_score) desc
            limit 1
            """,
            [str(results_path)],
        ).fetchone()

        top_sla = connection.execute(
            """
            select warehouse_name, carrier_name, week_start_date, sla_breach_rate, z_score
            from read_csv_auto(?, header = true)
            where detection_metric = 'sla_breach_rate'
                and anomaly_detected
            order by abs(z_score) desc
            limit 1
            """,
            [str(results_path)],
        ).fetchone()

        spike_segment = connection.execute(
            """
            select
                count(*) as shipments,
                sum(case when issue_type = 'damaged' then 1 else 0 end) as damaged_count,
                cast(sum(case when issue_type = 'damaged' then 1 else 0 end) as double)
                    / nullif(count(*), 0) as damaged_rate
            from fct_shipments
            where warehouse_id = ?
                and carrier_id = ?
                and order_purchase_date between ? and ?
            """,
            [
                spike_window["affected_warehouse_id"],
                spike_window["affected_carrier_id"],
                spike_window["start_date"],
                spike_window["end_date"],
            ],
        ).fetchone()

        outside_spike_segment = connection.execute(
            """
            select
                count(*) as shipments,
                sum(case when issue_type = 'damaged' then 1 else 0 end) as damaged_count,
                cast(sum(case when issue_type = 'damaged' then 1 else 0 end) as double)
                    / nullif(count(*), 0) as damaged_rate
            from fct_shipments
            where warehouse_id = ?
                and carrier_id = ?
                and not (order_purchase_date between ? and ?)
            """,
            [
                spike_window["affected_warehouse_id"],
                spike_window["affected_carrier_id"],
                spike_window["start_date"],
                spike_window["end_date"],
            ],
        ).fetchone()

        all_spike_window_damaged = connection.execute(
            """
            select sum(case when issue_type = 'damaged' then 1 else 0 end)
            from fct_shipments
            where order_purchase_date between ? and ?
            """,
            [spike_window["start_date"], spike_window["end_date"]],
        ).fetchone()[0]

        drift_warehouse = connection.execute(
            """
            select warehouse_name
            from dim_warehouse
            where warehouse_id = ?
            """,
            [drift_window["affected_warehouse_id"]],
        ).fetchone()[0]

        drift_start = connection.execute(
            """
            select
                count(*) as shipments,
                sum(case when sla_breach_flag then 1 else 0 end) as breach_count,
                cast(sum(case when sla_breach_flag then 1 else 0 end) as double)
                    / nullif(count(*), 0) as breach_rate
            from fct_shipments
            where warehouse_id = ?
                and order_purchase_date between cast(? as date)
                    and cast(? as date) + interval 6 day
            """,
            [drift_window["affected_warehouse_id"], drift_window["start_date"], drift_window["start_date"]],
        ).fetchone()

        drift_end = connection.execute(
            """
            select
                count(*) as shipments,
                sum(case when sla_breach_flag then 1 else 0 end) as breach_count,
                cast(sum(case when sla_breach_flag then 1 else 0 end) as double)
                    / nullif(count(*), 0) as breach_rate
            from fct_shipments
            where warehouse_id = ?
                and order_purchase_date between cast(? as date) - interval 6 day
                    and cast(? as date)
            """,
            [drift_window["affected_warehouse_id"], drift_window["end_date"], drift_window["end_date"]],
        ).fetchone()

    spike_share = (
        spike_segment[1] / all_spike_window_damaged
        if all_spike_window_damaged
        else None
    )

    findings = {
        "total_shipments": total_shipments,
        "date_start": date_start,
        "date_end": date_end,
        "total_flagged_segment_weeks": total_flagged_segment_weeks,
        "spike_detected": validation_rows[SPIKE_ANOMALY_ID]["detected"],
        "drift_detected": validation_rows[DRIFT_ANOMALY_ID]["detected"],
        "spike_first_week": validation_rows[SPIKE_ANOMALY_ID]["first_detected_week"],
        "drift_first_week": validation_rows[DRIFT_ANOMALY_ID]["first_detected_week"],
        "top_damaged_segment": (
            f"{top_damaged[0]} x {top_damaged[1]} on {top_damaged[2]} "
            f"(damaged issue rate {pct(top_damaged[3])}, z-score {top_damaged[4]:.2f})"
        ),
        "top_sla_segment": (
            f"{top_sla[0]} x {top_sla[1]} on {top_sla[2]} "
            f"(SLA breach rate {pct(top_sla[3])}, z-score {top_sla[4]:.2f})"
        ),
        "spike_shipments": spike_segment[0],
        "spike_damaged_count": spike_segment[1],
        "spike_damaged_rate": spike_segment[2],
        "outside_spike_shipments": outside_spike_segment[0],
        "outside_spike_damaged_count": outside_spike_segment[1],
        "outside_spike_damaged_rate": outside_spike_segment[2],
        "spike_damaged_share": spike_share,
        "drift_warehouse_name": drift_warehouse,
        "drift_start_shipments": drift_start[0],
        "drift_start_breaches": drift_start[1],
        "drift_start_rate": drift_start[2],
        "drift_end_shipments": drift_end[0],
        "drift_end_breaches": drift_end[1],
        "drift_end_rate": drift_end[2],
    }

    write_findings(findings_path, findings)

    print("Anomaly findings summary")
    print(f"Findings written to: {findings_path.relative_to(project_root)}")
    print(f"Total shipments analyzed: {number(total_shipments)}")
    print(f"Date range analyzed: {date_start} to {date_end}")
    print(f"Total flagged segment-weeks: {number(total_flagged_segment_weeks)}")
    print(
        f"{SPIKE_ANOMALY_ID}: detected={findings['spike_detected']}, "
        f"first_detected_week={findings['spike_first_week']}"
    )
    print(
        f"{DRIFT_ANOMALY_ID}: detected={findings['drift_detected']}, "
        f"first_detected_week={findings['drift_first_week']}"
    )
    print(f"Top damaged issue-rate anomaly: {findings['top_damaged_segment']}")
    print(f"Top SLA breach-rate anomaly: {findings['top_sla_segment']}")
    print(
        "Spike window Carrier B x Southeast FC damaged issue rate: "
        f"{pct(findings['spike_damaged_rate'])}"
    )
    print(
        "Same segment outside spike window damaged issue rate: "
        f"{pct(findings['outside_spike_damaged_rate'])}"
    )
    print(
        "Spike window damaged issue share from Carrier B x Southeast FC: "
        f"{pct(findings['spike_damaged_share'])}"
    )
    print(
        f"Drift warehouse {drift_warehouse} SLA breach rate start vs end: "
        f"{pct(findings['drift_start_rate'])} -> {pct(findings['drift_end_rate'])}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
