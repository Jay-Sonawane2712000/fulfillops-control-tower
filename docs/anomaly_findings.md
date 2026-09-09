# Anomaly Findings

## Executive Summary

This Day 4 analysis scored injected synthetic operational anomalies on top of real Olist order records. These are not real Olist business incidents; they are controlled signals generated for the FulfillOps Control Tower portfolio project.

- Total shipments analyzed: 32,150
- Date range analyzed: 2018-04-01 to 2018-08-29
- Total flagged segment-weeks: 54
- ANOM_SPIKE_001: detected=yes by damaged issue-rate detection; first detected week 2018-03-26
- ANOM_DRIFT_001: detected=yes by SLA breach-rate detection; first detected week 2018-06-25

## Top Flagged Segments

- Top damaged issue-rate anomaly: Central-West FC x Carrier A on 2018-08-06 (damaged issue rate 2.70%, z-score 4.48)
- Top SLA breach-rate anomaly: South FC x Carrier B on 2018-05-21 (SLA breach rate 100.00%, z-score 13.44)

## ANOM_SPIKE_001: Damaged Quality Spike

The injected spike targeted Carrier B x Southeast FC for damaged issues.

- Damaged issue rate during spike window: 30.04% (237 damaged issues across 789 shipments)
- Damaged issue rate for the same segment outside the spike window: 0.95% (71 damaged issues across 7,484 shipments)
- Share of damaged issues in the spike window attributable to Carrier B x Southeast FC: 88.76%

This explains why the original SLA-only detector missed the spike: the injected signal was about quality damage, not delivery lateness.

## ANOM_DRIFT_001: SLA Breach Drift

The injected drift targeted Central-West FC.

- SLA breach rate at the start of the drift window: 81.97% (50 breaches across 61 shipments)
- SLA breach rate at the end of the drift window: 81.98% (91 breaches across 111 shipments)
- First detected week: 2018-06-25

The start and end rates are nearly flat in the current generated data, so the finding should be framed as a detected synthetic SLA segment anomaly rather than a proven real-world deterioration. The drift detector uses a trailing four-week SLA breach baseline, so detection can appear after the pattern has begun rather than on the first affected day.
