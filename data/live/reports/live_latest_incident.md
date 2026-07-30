# KPI Incident Report

Generated at: `2026-07-30T09:05:30.404581+00:00`
Detector used: `residual_anomaly`
Incidents generated: **8**
Highest severity: **CRITICAL**

## Executive Summary

On 2026-07-11, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified de.wikipedia + desktop + spider as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

## Incident Table

| Incident ID | Date | KPI | Severity | Confidence | Top Root Cause |
|---|---:|---|---|---:|---|
| INC-20260711-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-11 | pageviews | CRITICAL | Medium (0.724) | de.wikipedia + desktop + spider |
| INC-20260729-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-29 | pageviews | CRITICAL | Medium (0.724) | en.wikipedia + mobile-web + automated |
| INC-20260724-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-24 | pageviews | CRITICAL | Medium (0.683) | en.wikipedia + mobile-web + automated |
| INC-20260725-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-25 | pageviews | CRITICAL | Medium (0.682) | en.wikipedia + mobile-web + automated |
| INC-20260728-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-28 | pageviews | CRITICAL | Medium (0.679) | en.wikipedia + mobile-web + automated |
| INC-20260727-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-27 | pageviews | CRITICAL | Medium (0.674) | en.wikipedia + mobile-web + automated |
| INC-20260726-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-26 | pageviews | CRITICAL | Medium (0.668) | en.wikipedia + mobile-web + automated |
| INC-20260720-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-20 | pageviews | WARNING | Medium (0.724) | ja.wikipedia + desktop + user |

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

## INC-20260729-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-07-29, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified en.wikipedia + mobile-web + automated as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: en.wikipedia + mobile-web + automated (100.0% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = en.wikipedia + mobile-web + automated; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `5518171.0`
- Expected value summary: `7819449.214286`
- Percent variance summary: `-0.294302`
- Anomaly rows: `1`

## INC-20260724-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-07-24, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified en.wikipedia + mobile-web + automated as the dominant contributor, explaining 83.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: en.wikipedia + mobile-web + automated (83.0% contribution)
- full_segment: ru.wikipedia + mobile-web + automated (17.0% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = en.wikipedia + mobile-web + automated; check recent releases, tracking changes, campaign mix, and operational issues.
- Review pageviews drivers for full_segment = ru.wikipedia + mobile-web + automated; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `3285565.5`
- Expected value summary: `5102045.839286`
- Percent variance summary: `-0.358106`
- Anomaly rows: `2`

## Limitations

- Live Wikimedia pageview data carries no ground-truth incident labels, so precision, recall and F1 cannot be computed for this track. Detector quality is measured on the labelled synthetic track instead.
- Traffic anomalies here are real but their causes are external and unverifiable - a spike may be a news event, a bot wave, or a Wikimedia infrastructure change. Root causes name the affected segment, not the reason.
- Recommended actions are rule based and should guide investigation, not prove causality.
