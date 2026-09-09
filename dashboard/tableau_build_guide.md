# Tableau Build Guide

This guide documents the Tableau Public dashboard structure for FulfillOps Control Tower using the curated CSV exports in `dashboard/exports/`.

The operational anomalies are synthetic signals layered on top of real Olist order records. Do not describe them as real Olist business incidents.

## Data Sources

Connect Tableau to these CSV files:

- `dashboard/exports/fct_shipments_dashboard.csv`
- `dashboard/exports/daily_sla_performance.csv`
- `dashboard/exports/weekly_quality_by_segment.csv`
- `dashboard/exports/anomaly_summary.csv`

## Tableau Calculated Fields

Create these calculated fields where needed.

### SLA Attainment %

Use with `daily_sla_performance.csv`:

```text
SUM([on_time_count]) / SUM([shipment_count])
```

Format as percentage.

### Quality Issue Rate %

Use with `weekly_quality_by_segment.csv`:

```text
SUM([issue_count]) / SUM([shipment_count])
```

Format as percentage.

### On-Time Delivery %

Use with `fct_shipments_dashboard.csv`:

```text
SUM(IF [real_late_delivery_flag] = FALSE THEN 1 ELSE 0 END) / COUNT([shipment_id])
```

Format as percentage.

### Avg Delay Days

Use with `fct_shipments_dashboard.csv` or `daily_sla_performance.csv`:

```text
AVG([delay_days])
```

### Anomaly Label

Use with `fct_shipments_dashboard.csv` or `weekly_quality_by_segment.csv`:

```text
IF [anomaly_flag] = "none" THEN "No injected anomaly" ELSE [anomaly_flag] END
```

For `weekly_quality_by_segment.csv`, use `[dominant_anomaly_flag]` in the same pattern.

## Page 1: Executive Summary

Suggested title: `FulfillOps Control Tower`

Suggested subtitle: `SLA performance, quality issues, and injected anomaly signals across synthetic operations layered on real Olist orders`

Dataset to use:

- Primary: `daily_sla_performance.csv`
- Supporting: `anomaly_summary.csv`

KPI cards:

- Total shipments: `SUM([shipment_count])`
- SLA Attainment %: calculated field `SLA Attainment %`
- SLA breach count: `SUM([sla_breach_count])`
- Avg Delay Days: `AVG([avg_delay_days])`
- Real late delivery count: `SUM([real_late_delivery_count])`

Charts to create:

- Daily SLA attainment trend: `order_purchase_date` on Columns, `SLA Attainment %` on Rows, color by `warehouse_name`
- SLA breach count by warehouse: `warehouse_name` on Rows, `SUM([sla_breach_count])` on Columns
- Carrier SLA comparison: `carrier_name` on Rows, `SLA Attainment %` on Columns, color by `sla_tier`
- Known anomaly summary table: from `anomaly_summary.csv`, show `anomaly_id`, `validation_metric`, `detected`, `first_detected_week`, and `flagged_segment_weeks`

Filters to add:

- `order_purchase_date`
- `warehouse_name`
- `carrier_name`
- `sla_tier`

Headline annotation:

- `Carrier B x Southeast FC drove 88.76% of damaged issues in the injected spike window.`

Suggested screenshot/export filename:

- `dashboard/screenshots/executive_summary.png`

## Page 2: Ops Drill-down

Suggested title: `Ops Drill-down`

Suggested subtitle: `Shipment-level performance by warehouse, carrier, SLA tier, and product category`

Dataset to use:

- Primary: `fct_shipments_dashboard.csv`

KPI cards:

- Shipment count: `COUNT([shipment_id])`
- On-Time Delivery %: calculated field `On-Time Delivery %`
- SLA breach rate: `SUM(IF [sla_breach_flag] = TRUE THEN 1 ELSE 0 END) / COUNT([shipment_id])`
- Avg Delay Days: calculated field `Avg Delay Days`
- Quality issue count: `SUM(IF [quality_issue_flag] = TRUE THEN 1 ELSE 0 END)`

Charts to create:

- Shipment volume over time: `order_purchase_date` on Columns, `COUNT([shipment_id])` on Rows
- Delay distribution: `delay_days` as bins on Columns, `COUNT([shipment_id])` on Rows
- SLA breaches by warehouse and carrier: `warehouse_name` on Rows, `carrier_name` on Columns, color by `AVG(INT([sla_breach_flag]))`
- Category SLA view: `category_name` on Rows, `COUNT([shipment_id])` and `AVG([actual_delivery_days])` on Columns
- Shipment detail table: `order_id`, `warehouse_name`, `carrier_name`, `category_name`, `sla_tier`, `actual_delivery_days`, `sla_target_days`, `issue_type`, and `anomaly_flag`

Filters to add:

- `order_purchase_date`
- `warehouse_name`
- `carrier_name`
- `category_name`
- `sla_tier`
- `issue_type`
- calculated field `Anomaly Label`

Suggested screenshot/export filename:

- `dashboard/screenshots/ops_drilldown.png`

## Page 3: Root-cause/Anomaly View

Suggested title: `Root-cause and Anomaly View`

Suggested subtitle: `Weekly quality and SLA anomaly signals by operational segment`

Datasets to use:

- Primary: `weekly_quality_by_segment.csv`
- Supporting: `anomaly_summary.csv`
- Optional drill-through: `fct_shipments_dashboard.csv`

KPI cards:

- Weekly shipment count: `SUM([shipment_count])`
- Quality Issue Rate %: calculated field `Quality Issue Rate %`
- Issue count: `SUM([issue_count])`
- Anomaly count: `SUM([anomaly_count])`
- Detected known anomalies: count rows in `anomaly_summary.csv` where `[detected] = "yes"`

Charts to create:

- Weekly quality issue rate trend: `week_start_date` on Columns, `Quality Issue Rate %` on Rows, color by `issue_type`
- Damaged issue spike view: filter `issue_type = "damaged"`, show `week_start_date` by `Quality Issue Rate %`, color by `carrier_name`, filter or highlight `warehouse_name = "Southeast FC"`
- Segment heatmap: `warehouse_name` on Rows, `carrier_name` on Columns, color by `Quality Issue Rate %`
- Category issue breakdown: `category_name` on Rows, `SUM([issue_count])` on Columns, color by `issue_type`
- Anomaly validation table: from `anomaly_summary.csv`, show `anomaly_id`, `validation_metric`, `detected`, `first_detected_week`, `flagged_segment_weeks`, and `top_flagged_segments`

Filters to add:

- `week_start_date`
- `warehouse_name`
- `carrier_name`
- `category_name`
- `issue_type`
- `dominant_anomaly_flag`

Required story callout:

- `Carrier B x Southeast FC drove 88.76% of damaged issues in the spike window. This is an injected synthetic quality anomaly layered on real Olist order volume.`

Suggested screenshot/export filename:

- `dashboard/screenshots/root_cause_anomaly.png`
