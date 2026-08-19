# KPI Incident Report

Generated at: `2026-08-19T07:08:17.634498+00:00`
Detector used: `residual_anomaly`
Incidents generated: **2**
Highest severity: **CRITICAL**

## Executive Summary

On 2026-07-27, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified en.wikipedia + mobile-web + automated as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

## Incident Table

| Incident ID | Date | KPI | Severity | Confidence | Top Root Cause |
|---|---:|---|---|---:|---|
| INC-20260727-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-27 | pageviews | CRITICAL | Medium (0.723) | en.wikipedia + mobile-web + automated |
| INC-20260728-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-07-28 | pageviews | CRITICAL | Medium (0.723) | en.wikipedia + mobile-web + automated |

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

## INC-20260728-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-07-28, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified en.wikipedia + mobile-web + automated as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: en.wikipedia + mobile-web + automated (100.0% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = en.wikipedia + mobile-web + automated; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `5209354.0`
- Expected value summary: `7966696.678571`
- Percent variance summary: `-0.346109`
- Anomaly rows: `1`

## Limitations

- Live Wikimedia pageview data carries no ground-truth incident labels, so precision, recall and F1 cannot be computed for this track. Detector quality is measured on the labelled synthetic track instead.
- Traffic anomalies here are real but their causes are external and unverifiable - a spike may be a news event, a bot wave, or a Wikimedia infrastructure change. Root causes name the affected segment, not the reason.
- Recommended actions are rule based and should guide investigation, not prove causality.
