# Dashboard Exports

The CSV files in `dashboard/exports/` are curated Tableau inputs generated from DuckDB marts.

Use `dashboard/tableau_build_guide.md` for the exact Tableau Public dashboard structure, calculated fields, filters, and suggested screenshots.

## Export Files

- `fct_shipments_dashboard.csv`: shipment-level fact export for drill-down analysis, SLA flags, quality issue flags, and anomaly labels.
- `daily_sla_performance.csv`: daily SLA performance by warehouse, carrier, and SLA tier for trend and scorecard views.
- `weekly_quality_by_segment.csv`: weekly quality issue rates by warehouse, carrier, category, and issue type for root-cause analysis.
- `anomaly_summary.csv`: compact known-anomaly validation summary for annotation and story points.

## Regenerate Exports

From the project root, run:

```text
python scripts/export_tableau_datasets.py
```

## Suggested Tableau Pages

- Executive Summary
- Ops Drill-down
- Root-cause/Anomaly View
