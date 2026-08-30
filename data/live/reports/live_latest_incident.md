# KPI Incident Report

Generated at: `2026-08-30T11:58:29.940097+00:00`
Detector used: `residual_anomaly`
Incidents generated: **10**
Highest severity: **CRITICAL**

## Executive Summary

On 2026-08-24, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified ja.wikipedia + desktop + spider as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

## Incident Table

| Incident ID | Date | KPI | Severity | Confidence | Top Root Cause |
|---|---:|---|---|---:|---|
| INC-20260824-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-24 | pageviews | CRITICAL | Medium (0.757) | ja.wikipedia + desktop + spider |
| INC-20260826-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-26 | pageviews | CRITICAL | Medium (0.727) | ja.wikipedia + desktop + spider |
| INC-20260818-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-18 | pageviews | CRITICAL | Medium (0.722) | de.wikipedia + mobile-web + spider |
| INC-20260820-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-20 | pageviews | CRITICAL | Medium (0.722) | de.wikipedia + mobile-app + automated |
| INC-20260825-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-25 | pageviews | CRITICAL | Medium (0.719) | ja.wikipedia + desktop + spider |
| INC-20260823-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-23 | pageviews | CRITICAL | Medium (0.715) | ru.wikipedia + desktop + automated |
| INC-20260827-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-27 | pageviews | CRITICAL | Medium (0.657) | ja.wikipedia + desktop + spider |
| INC-20260829-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-29 | pageviews | CRITICAL | Medium (0.618) | ja.wikipedia + desktop + spider |
| INC-20260828-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-28 | pageviews | CRITICAL | Medium (0.618) | ja.wikipedia + desktop + spider |
| INC-20260819-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-19 | pageviews | CRITICAL | Medium (0.590) | fr.wikipedia + mobile-web + spider |

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

## INC-20260826-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-08-26, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified ja.wikipedia + desktop + spider as the dominant contributor, explaining 94.9% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: ja.wikipedia + desktop + spider (94.9% contribution)
- full_segment: de.wikipedia + mobile-web + spider (5.0% contribution)
- full_segment: de.wikipedia + mobile-app + automated (0.1% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = ja.wikipedia + desktop + spider; check recent releases, tracking changes, campaign mix, and operational issues.
- Review pageviews drivers for full_segment = de.wikipedia + mobile-web + spider; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `1897570.333333`
- Expected value summary: `2497215.452381`
- Percent variance summary: `-0.238309`
- Anomaly rows: `3`

## INC-20260818-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-08-18, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified de.wikipedia + mobile-web + spider as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: de.wikipedia + mobile-web + spider (100.0% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = de.wikipedia + mobile-web + spider; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `1628597.0`
- Expected value summary: `1935316.035714`
- Percent variance summary: `-0.158485`
- Anomaly rows: `1`

## Limitations

- Live Wikimedia pageview data carries no ground-truth incident labels, so precision, recall and F1 cannot be computed for this track. Detector quality is measured on the labelled synthetic track instead.
- Traffic anomalies here are real but their causes are external and unverifiable - a spike may be a news event, a bot wave, or a Wikimedia infrastructure change. Root causes name the affected segment, not the reason.
- Recommended actions are rule based and should guide investigation, not prove causality.
