# KPI Incident Report

Generated at: `2026-08-03T10:08:55.861791+00:00`
Detector used: `residual_anomaly`
Incidents generated: **9**
Highest severity: **CRITICAL**

## Executive Summary

On 2026-07-24, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified en.wikipedia + mobile-web + automated as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

## Incident Table

| Incident ID | Date | KPI | Severity | Confidence | Top Root Cause |
|---|---:|---|---|---:|---|
| INC-20260724-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-24 | pageviews | CRITICAL | Medium (0.709) | en.wikipedia + mobile-web + automated |
| INC-20260725-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-25 | pageviews | CRITICAL | Medium (0.709) | en.wikipedia + mobile-web + automated |
| INC-20260727-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-27 | pageviews | CRITICAL | Medium (0.709) | en.wikipedia + mobile-web + automated |
| INC-20260728-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-28 | pageviews | CRITICAL | Medium (0.709) | en.wikipedia + mobile-web + automated |
| INC-20260729-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-29 | pageviews | CRITICAL | Medium (0.709) | en.wikipedia + mobile-web + automated |
| INC-20260730-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-30 | pageviews | CRITICAL | Medium (0.709) | en.wikipedia + mobile-web + automated |
| INC-20260731-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-31 | pageviews | CRITICAL | Medium (0.709) | en.wikipedia + mobile-web + automated |
| INC-20260801-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-01 | pageviews | CRITICAL | Medium (0.709) | en.wikipedia + mobile-web + automated |
| INC-20260720-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-20 | pageviews | WARNING | Medium (0.709) | ja.wikipedia + desktop + user |

## INC-20260724-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-07-24, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified en.wikipedia + mobile-web + automated as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: en.wikipedia + mobile-web + automated (100.0% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = en.wikipedia + mobile-web + automated; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `5481351.0`
- Expected value summary: `8498046.714286`
- Percent variance summary: `-0.354987`
- Anomaly rows: `1`

## INC-20260725-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-07-25, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified en.wikipedia + mobile-web + automated as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: en.wikipedia + mobile-web + automated (100.0% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = en.wikipedia + mobile-web + automated; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `5339831.0`
- Expected value summary: `8353276.821429`
- Percent variance summary: `-0.36075`
- Anomaly rows: `1`

## INC-20260727-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-07-27, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified en.wikipedia + mobile-web + automated as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: en.wikipedia + mobile-web + automated (100.0% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = en.wikipedia + mobile-web + automated; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `5195889.0`
- Expected value summary: `8103232.071429`
- Percent variance summary: `-0.358788`
- Anomaly rows: `1`

## Limitations

- Live Wikimedia pageview data carries no ground-truth incident labels, so precision, recall and F1 cannot be computed for this track. Detector quality is measured on the labelled synthetic track instead.
- Traffic anomalies here are real but their causes are external and unverifiable - a spike may be a news event, a bot wave, or a Wikimedia infrastructure change. Root causes name the affected segment, not the reason.
- Recommended actions are rule based and should guide investigation, not prove causality.
