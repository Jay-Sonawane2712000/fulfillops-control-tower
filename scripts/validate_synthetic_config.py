import csv
from pathlib import Path


CONFIG_SPECS = {
    "warehouses.csv": {
        "columns": {
            "warehouse_id",
            "warehouse_name",
            "assigned_states",
            "region_rule_notes",
        },
        "expected_rows": 4,
        "label": "warehouses",
    },
    "carriers.csv": {
        "columns": {
            "carrier_id",
            "carrier_name",
            "reliability_tier",
            "performance_notes",
            "warehouse_exception",
        },
        "expected_rows": 4,
        "label": "carriers",
    },
    "sla_targets.csv": {
        "columns": {
            "sla_tier",
            "target_days",
            "description",
        },
        "expected_rows": 3,
        "label": "SLA tiers",
    },
    "anomaly_windows.csv": {
        "columns": {
            "anomaly_id",
            "anomaly_type",
            "affected_carrier_id",
            "affected_warehouse_id",
            "issue_type",
            "start_date",
            "end_date",
            "notes",
        },
        "expected_rows": 2,
        "label": "anomaly windows",
    },
}


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return reader.fieldnames or [], list(reader)


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    synthetic_dir = project_root / "raw" / "synthetic"
    failures = []

    print("Synthetic operations config validation")
    print(f"Expected folder: {synthetic_dir.relative_to(project_root)}")

    for filename, spec in CONFIG_SPECS.items():
        path = synthetic_dir / filename

        if not path.is_file():
            failures.append(f"{filename}: file is missing")
            continue

        columns, rows = read_csv_rows(path)
        missing_columns = spec["columns"] - set(columns)
        if missing_columns:
            failures.append(
                f"{filename}: missing columns: {', '.join(sorted(missing_columns))}"
            )

        expected_rows = spec["expected_rows"]
        if len(rows) != expected_rows:
            failures.append(
                f"{filename}: expected {expected_rows} {spec['label']}, found {len(rows)}"
            )

    if failures:
        print("\nFAIL: Synthetic config is not ready.")
        print("\nIssues:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASS: Synthetic config files are present and match expected structure.")
    for filename, spec in CONFIG_SPECS.items():
        print(f"- {filename}: {spec['expected_rows']} {spec['label']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
