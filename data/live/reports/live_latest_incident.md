# KPI Incident Report

Generated at: `2026-08-27T17:41:03.395785+00:00`
Detector used: `residual_anomaly`
Incidents generated: **6**
Highest severity: **CRITICAL**

## Executive Summary

On 2026-08-24, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified ja.wikipedia + desktop + spider as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

## Incident Table

| Incident ID | Date | KPI | Severity | Confidence | Top Root Cause |
|---|---:|---|---|---:|---|
| INC-20260824-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-24 | pageviews | CRITICAL | Medium (0.758) | ja.wikipedia + desktop + spider |
| INC-20260825-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-25 | pageviews | CRITICAL | Medium (0.732) | ja.wikipedia + desktop + spider |
| INC-20260826-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-26 | pageviews | CRITICAL | Medium (0.732) | ja.wikipedia + desktop + spider |
| INC-20260820-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-20 | pageviews | CRITICAL | Medium (0.723) | de.wikipedia + mobile-app + automated |
| INC-20260823-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-23 | pageviews | CRITICAL | Medium (0.723) | de.wikipedia + mobile-app + automated |
| INC-20260819-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-19 | pageviews | WARNING | Medium (0.555) | de.wikipedia + mobile-web + spider |

## INC-20260824-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-08-24, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified ja.wikipedia + desktop + spider as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: ja.wikipedia + desktop + spider (100.0% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = ja.wikipedia + desktop + spider; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `3813824.0`
- Expected value summary: `5727009.464286`
- Percent variance summary: `-0.334064`
- Anomaly rows: `1`

## INC-20260825-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-08-25, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified ja.wikipedia + desktop + spider as the dominant contributor, explaining 99.9% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: ja.wikipedia + desktop + spider (99.9% contribution)
- full_segment: de.wikipedia + mobile-app + automated (0.1% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = ja.wikipedia + desktop + spider; check recent releases, tracking changes, campaign mix, and operational issues.
- Review pageviews drivers for full_segment = de.wikipedia + mobile-app + automated; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `1958614.0`
- Expected value summary: `2835460.25`
- Percent variance summary: `-0.365047`
- Anomaly rows: `2`

## INC-20260826-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-08-26, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified ja.wikipedia + desktop + spider as the dominant contributor, explaining 99.9% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: ja.wikipedia + desktop + spider (99.9% contribution)
- full_segment: de.wikipedia + mobile-app + automated (0.1% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = ja.wikipedia + desktop + spider; check recent releases, tracking changes, campaign mix, and operational issues.
- Review pageviews drivers for full_segment = de.wikipedia + mobile-app + automated; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `1954036.0`
- Expected value summary: `2808535.928571`
- Percent variance summary: `-0.333475`
- Anomaly rows: `2`

## Limitations

- Live Wikimedia pageview data carries no ground-truth incident labels, so precision, recall and F1 cannot be computed for this track. Detector quality is measured on the labelled synthetic track instead.
- Traffic anomalies here are real but their causes are external and unverifiable - a spike may be a news event, a bot wave, or a Wikimedia infrastructure change. Root causes name the affected segment, not the reason.
- Recommended actions are rule based and should guide investigation, not prove causality.
