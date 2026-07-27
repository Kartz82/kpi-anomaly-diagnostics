# KPI Incident Report

Generated at: `2026-07-27T14:55:50.899420+00:00`
Detector used: `residual_anomaly`
Incidents generated: **12**
Highest severity: **CRITICAL**

## Executive Summary

On 2026-07-03, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified de.wikipedia + desktop + spider as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

## Incident Table

| Incident ID | Date | KPI | Severity | Confidence | Top Root Cause |
|---|---:|---|---|---:|---|
| INC-20260703-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-03 | pageviews | CRITICAL | Medium (0.759) | de.wikipedia + desktop + spider |
| INC-20260711-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-11 | pageviews | CRITICAL | Medium (0.759) | de.wikipedia + desktop + spider |
| INC-20260702-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-02 | pageviews | CRITICAL | Medium (0.724) | de.wikipedia + desktop + spider |
| INC-20260704-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-04 | pageviews | CRITICAL | Medium (0.724) | de.wikipedia + desktop + spider |
| INC-20260705-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-05 | pageviews | CRITICAL | Medium (0.724) | de.wikipedia + desktop + spider |
| INC-20260706-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-06 | pageviews | CRITICAL | Medium (0.724) | de.wikipedia + desktop + spider |
| INC-20260707-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-07 | pageviews | CRITICAL | Medium (0.724) | de.wikipedia + desktop + spider |
| INC-20260708-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-08 | pageviews | CRITICAL | Medium (0.724) | de.wikipedia + desktop + spider |
| INC-20260709-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-09 | pageviews | CRITICAL | Medium (0.724) | de.wikipedia + desktop + spider |
| INC-20260710-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-10 | pageviews | CRITICAL | Medium (0.724) | de.wikipedia + desktop + spider |
| INC-20260712-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-12 | pageviews | CRITICAL | Medium (0.724) | de.wikipedia + desktop + spider |
| INC-20260713-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-13 | pageviews | CRITICAL | Medium (0.724) | de.wikipedia + desktop + spider |

## INC-20260703-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-07-03, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified de.wikipedia + desktop + spider as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: de.wikipedia + desktop + spider (100.0% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = de.wikipedia + desktop + spider; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `2825251.0`
- Expected value summary: `3818810.5`
- Percent variance summary: `-0.260175`
- Anomaly rows: `1`

## INC-20260711-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-07-11, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified de.wikipedia + desktop + spider as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: de.wikipedia + desktop + spider (100.0% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = de.wikipedia + desktop + spider; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `2400321.0`
- Expected value summary: `3707341.5`
- Percent variance summary: `-0.352549`
- Anomaly rows: `1`

## INC-20260702-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-07-02, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified de.wikipedia + desktop + spider as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: de.wikipedia + desktop + spider (100.0% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = de.wikipedia + desktop + spider; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `3064204.0`
- Expected value summary: `3816935.964286`
- Percent variance summary: `-0.197208`
- Anomaly rows: `1`

## Limitations

- Live Wikimedia pageview data carries no ground-truth incident labels, so precision, recall and F1 cannot be computed for this track. Detector quality is measured on the labelled synthetic track instead.
- Traffic anomalies here are real but their causes are external and unverifiable - a spike may be a news event, a bot wave, or a Wikimedia infrastructure change. Root causes name the affected segment, not the reason.
- Recommended actions are rule based and should guide investigation, not prove causality.
