import csv
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path


EXPECTED_FILES = {
    "warehouse_assignments.csv",
    "carrier_assignments.csv",
    "issue_flags.csv",
    "order_sla_targets.csv",
}
ACCEPTED_ISSUE_TYPES = {
    "none",
    "missing",
    "damaged",
    "wrong",
    "failed",
    "cancelled",
    "refund",
}
EXPECTED_ANOMALY_FLAGS = {"ANOM_SPIKE_001", "ANOM_DRIFT_001"}


def parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def last_six_complete_month_window(purchase_dates: list[date]) -> tuple[date, date]:
    max_date = max(purchase_dates)
    latest_month_start = date(max_date.year, max_date.month, 1)
    latest_complete_month_start = (
        latest_month_start if max_date.day >= 28 else add_months(latest_month_start, -1)
    )
    start_date = add_months(latest_complete_month_start, -5)
    end_date = add_months(latest_complete_month_start, 1) - timedelta(days=1)
    return start_date, end_date


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def expected_order_count(project_root: Path) -> int:
    orders = read_rows(project_root / "raw" / "olist" / "olist_orders_dataset.csv")
    purchase_dates = [
        parse_datetime(order["order_purchase_timestamp"]).date()
        for order in orders
        if order["order_purchase_timestamp"]
    ]
    start_date, end_date = last_six_complete_month_window(purchase_dates)
    return sum(
        1
        for order in orders
        if start_date
        <= parse_datetime(order["order_purchase_timestamp"]).date()
        <= end_date
    )


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    generated_dir = project_root / "raw" / "synthetic" / "generated"
    failures = []

    print("Synthetic operations output validation")
    print(f"Expected folder: {generated_dir.relative_to(project_root)}")

    expected_count = expected_order_count(project_root)
    file_rows = {}

    for filename in sorted(EXPECTED_FILES):
        path = generated_dir / filename
        if not path.is_file():
            failures.append(f"{filename}: file is missing")
            continue

        rows = read_rows(path)
        file_rows[filename] = rows
        if len(rows) != expected_count:
            failures.append(
                f"{filename}: expected {expected_count} rows, found {len(rows)}"
            )

        if not rows or "order_id" not in rows[0]:
            failures.append(f"{filename}: order_id column is missing")
        elif any(not row["order_id"] for row in rows):
            failures.append(f"{filename}: order_id contains null or blank values")

    issue_rows = file_rows.get("issue_flags.csv", [])
    issue_types = Counter(row["issue_type"] for row in issue_rows)
    invalid_issue_types = set(issue_types) - ACCEPTED_ISSUE_TYPES
    if invalid_issue_types:
        failures.append(
            "issue_flags.csv: invalid issue_type values: "
            + ", ".join(sorted(invalid_issue_types))
        )

    anomaly_flags = Counter(row["anomaly_flag"] for row in issue_rows)
    missing_anomaly_flags = EXPECTED_ANOMALY_FLAGS - set(anomaly_flags)
    if missing_anomaly_flags:
        failures.append(
            "issue_flags.csv: missing expected anomaly_flag labels: "
            + ", ".join(sorted(missing_anomaly_flags))
        )

    if failures:
        print("\nFAIL: Synthetic outputs are not ready.")
        print("\nIssues:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASS: Synthetic outputs are present and match expected structure.")
    print(f"Expected filtered order count: {expected_count}")
    for filename in sorted(EXPECTED_FILES):
        print(f"- {filename}: {len(file_rows[filename])} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
