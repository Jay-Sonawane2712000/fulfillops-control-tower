# Anomaly Detection Notes

## Method

The Day 4 workflow uses two anomaly detection tracks by warehouse-carrier segment.

The SLA breach detector looks for unusual weekly SLA breach rates. For each segment-week, it compares the current SLA breach rate against that same segment's previous four weeks. This track is designed to catch delivery and SLA drift.

The damaged issue-rate detector looks for unusual weekly damaged-item rates. It compares each segment-week's damaged issue rate against that segment's overall weekly pattern. This track is designed to catch quality spikes that may not affect delivery timing.

Both tracks output a z-score. A higher absolute z-score means the current week is farther from the relevant baseline for that segment.

## Threshold And Volume Rules

The SLA breach detector flags a segment-week when:

- absolute z-score is at least 2
- shipment count is at least 20
- at least four prior weeks are available for the segment
- the prior four-week standard deviation is greater than zero

The damaged issue-rate detector uses the same z-score threshold and minimum shipment count, but compares against the segment's broader weekly quality pattern. This avoids missing quality spikes that occur at the start of the six-month generated window, where four prior weeks are not available.

These rules reduce false positives from very small segment groups.

## Detection Outputs

`warehouse/anomaly_results.csv` is a generated detailed scoring file with one row per warehouse-carrier segment-week per detection metric. It is generated output and is not committed.

`warehouse/anomaly_validation_summary.csv` is a small summary artifact that reports whether each known injected anomaly label was detected, the first detected week, flagged segment-week counts, and top flagged segments by z-score.

## Known Anomaly Validation

The workflow compares scored anomalies against injected labels only after scoring. It validates `ANOM_SPIKE_001` against the damaged issue-rate detector and `ANOM_DRIFT_001` against the SLA breach detector.

The current run scored both SLA breach rate and damaged issue rate. `ANOM_SPIKE_001` was detected by the damaged issue-rate detector. `ANOM_DRIFT_001` was detected by the SLA breach detector.

The sharp spike was injected as a damaged-issue spike, so it does not necessarily produce a clean SLA breach anomaly. The gradual drift can be detected late because the trailing four-week baseline adapts as the drift unfolds.
