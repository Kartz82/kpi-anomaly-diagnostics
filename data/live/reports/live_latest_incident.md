# KPI Incident Report

Generated at: `2026-09-03T11:18:57.415404+00:00`
Detector used: `residual_anomaly`
Incidents generated: **12**
Highest severity: **CRITICAL**

## Executive Summary

On 2026-09-01, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified ja.wikipedia + desktop + spider as the dominant contributor, explaining 72.9% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

## Incident Table

| Incident ID | Date | KPI | Severity | Confidence | Top Root Cause |
|---|---:|---|---|---:|---|
| INC-20260901-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-09-01 | pageviews | CRITICAL | Medium (0.726) | ja.wikipedia + desktop + spider |
| INC-20260823-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-23 | pageviews | CRITICAL | Medium (0.722) | ru.wikipedia + desktop + automated |
| INC-20260825-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-25 | pageviews | CRITICAL | Medium (0.681) | ja.wikipedia + desktop + spider |
| INC-20260826-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-26 | pageviews | CRITICAL | Medium (0.674) | ja.wikipedia + desktop + spider |
| INC-20260824-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-24 | pageviews | CRITICAL | Medium (0.666) | ja.wikipedia + desktop + spider |
| INC-20260828-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-28 | pageviews | CRITICAL | Medium (0.663) | ja.wikipedia + desktop + spider |
| INC-20260827-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-27 | pageviews | CRITICAL | Medium (0.657) | ja.wikipedia + desktop + spider |
| INC-20260829-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-29 | pageviews | CRITICAL | Medium (0.653) | ja.wikipedia + desktop + spider |
| INC-20260831-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-31 | pageviews | CRITICAL | Medium (0.644) | ja.wikipedia + desktop + spider |
| INC-20260902-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-09-02 | pageviews | CRITICAL | Medium (0.643) | ja.wikipedia + desktop + spider |
| INC-20260830-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-30 | pageviews | CRITICAL | Medium (0.637) | ja.wikipedia + desktop + spider |
| INC-20260821-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-21 | pageviews | WARNING | Medium (0.722) | ru.wikipedia + desktop + automated |

## INC-20260901-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-09-01, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified ja.wikipedia + desktop + spider as the dominant contributor, explaining 72.9% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: ja.wikipedia + desktop + spider (72.9% contribution)
- full_segment: fr.wikipedia + mobile-web + spider (11.1% contribution)
- full_segment: de.wikipedia + mobile-web + spider (8.0% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = ja.wikipedia + desktop + spider; check recent releases, tracking changes, campaign mix, and operational issues.
- Review pageviews drivers for full_segment = fr.wikipedia + mobile-web + spider; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `1364958.833333`
- Expected value summary: `1641676.928571`
- Percent variance summary: `-0.215194`
- Anomaly rows: `6`

## INC-20260823-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-08-23, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified ru.wikipedia + desktop + automated as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: ru.wikipedia + desktop + automated (100.0% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = ru.wikipedia + desktop + automated; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `4274159.0`
- Expected value summary: `5868586.714286`
- Percent variance summary: `-0.271689`
- Anomaly rows: `1`

## INC-20260825-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-08-25, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified ja.wikipedia + desktop + spider as the dominant contributor, explaining 68.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: ja.wikipedia + desktop + spider (68.0% contribution)
- full_segment: ru.wikipedia + desktop + automated (31.9% contribution)
- full_segment: de.wikipedia + mobile-app + automated (0.1% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = ja.wikipedia + desktop + spider; check recent releases, tracking changes, campaign mix, and operational issues.
- Review pageviews drivers for full_segment = ru.wikipedia + desktop + automated; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `2937046.0`
- Expected value summary: `3795823.083333`
- Percent variance summary: `-0.291333`
- Anomaly rows: `3`

## Limitations

- Live Wikimedia pageview data carries no ground-truth incident labels, so precision, recall and F1 cannot be computed for this track. Detector quality is measured on the labelled synthetic track instead.
- Traffic anomalies here are real but their causes are external and unverifiable - a spike may be a news event, a bot wave, or a Wikimedia infrastructure change. Root causes name the affected segment, not the reason.
- Recommended actions are rule based and should guide investigation, not prove causality.
