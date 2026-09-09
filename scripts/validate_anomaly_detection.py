import csv
from pathlib import Path


EXPECTED_ANOMALIES = {"ANOM_SPIKE_001", "ANOM_DRIFT_001"}
REQUIRED_RESULT_COLUMNS = {
    "week_start_date",
    "warehouse_id",
    "warehouse_name",
    "carrier_id",
    "carrier_name",
    "shipment_count",
    "sla_breach_count",
    "sla_breach_rate",
    "trailing_4_week_mean",
    "trailing_4_week_std",
    "z_score",
    "anomaly_detected",
    "known_anomaly_labels",
}
REQUIRED_SUMMARY_COLUMNS = {
    "anomaly_id",
    "detected",
    "first_detected_week",
    "flagged_segment_weeks",
    "top_flagged_segments",
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return reader.fieldnames or [], list(reader)


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    results_path = project_root / "warehouse" / "anomaly_results.csv"
    summary_path = project_root / "warehouse" / "anomaly_validation_summary.csv"
    failures = []

    print("Anomaly detection validation")

    if not results_path.is_file():
        failures.append("warehouse/anomaly_results.csv is missing")
    if not summary_path.is_file():
        failures.append("warehouse/anomaly_validation_summary.csv is missing")

    result_rows = []
    if results_path.is_file():
        result_columns, result_rows = read_csv(results_path)
        missing_result_columns = REQUIRED_RESULT_COLUMNS - set(result_columns)
        if missing_result_columns:
            failures.append(
                "anomaly_results.csv missing columns: "
                + ", ".join(sorted(missing_result_columns))
            )
        if not result_rows:
            failures.append("anomaly_results.csv has no rows")

    summary_rows = []
    if summary_path.is_file():
        summary_columns, summary_rows = read_csv(summary_path)
        missing_summary_columns = REQUIRED_SUMMARY_COLUMNS - set(summary_columns)
        if missing_summary_columns:
            failures.append(
                "anomaly_validation_summary.csv missing columns: "
                + ", ".join(sorted(missing_summary_columns))
            )

        summary_anomalies = {row["anomaly_id"] for row in summary_rows}
        missing_anomalies = EXPECTED_ANOMALIES - summary_anomalies
        if missing_anomalies:
            failures.append(
                "validation summary missing expected anomaly IDs: "
                + ", ".join(sorted(missing_anomalies))
            )

    if failures:
        print("\nFAIL: Anomaly detection outputs are not ready.")
        print("\nIssues:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    flagged_count = sum(
        1 for row in result_rows if row["anomaly_detected"].lower() == "true"
    )

    print("\nPASS: Anomaly detection outputs are present and structurally valid.")
    print(f"Segment-weeks scored: {len(result_rows)}")
    print(f"Flagged segment-weeks: {flagged_count}")
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
