# Anomaly Detection Notes

## Method

The Day 4 detector looks for unusual weekly SLA breach rates by warehouse-carrier segment. For each segment-week, it compares the current SLA breach rate against that same segment's previous four weeks.

The output is a z-score. A higher absolute z-score means the current week is farther from the recent baseline for that segment.

## Threshold And Volume Rules

The detector flags a segment-week when:

- absolute z-score is at least 2
- shipment count is at least 20
- at least four prior weeks are available for the segment
- the prior four-week standard deviation is greater than zero

These rules reduce false positives from very small or brand-new segment groups.

## Detection Outputs

`warehouse/anomaly_results.csv` is a generated detailed scoring file with one row per warehouse-carrier segment-week. It is generated output and is not committed.

`warehouse/anomaly_validation_summary.csv` is a small summary artifact that reports whether each known injected anomaly label was detected, the first detected week, flagged segment-week counts, and top flagged segments by z-score.

## Known Anomaly Validation

The workflow compares detected SLA breach anomalies against the injected labels `ANOM_SPIKE_001` and `ANOM_DRIFT_001` from the synthetic layer.

The current run scored 353 warehouse-carrier segment-weeks and flagged 40 segment-weeks. `ANOM_DRIFT_001` was detected, with the first detected week starting 2018-06-25. `ANOM_SPIKE_001` was not detected by this SLA-breach method.

The sharp spike was injected as a damaged-issue spike, so it does not necessarily produce a clean SLA breach anomaly. The gradual drift can also be detected late because the trailing four-week baseline adapts as the drift unfolds.
