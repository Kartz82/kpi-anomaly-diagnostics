# KPI Incident Report

Generated at: `2026-08-15T07:00:22.632284+00:00`
Detector used: `residual_anomaly`
Incidents generated: **1**
Highest severity: **CRITICAL**

## Executive Summary

On 2026-08-12, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified ru.wikipedia + mobile-web + automated as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

## Incident Table

| Incident ID | Date | KPI | Severity | Confidence | Top Root Cause |
|---|---:|---|---|---:|---|
| INC-20260812-PAGEVIEWS-RESIDUAL-ANOMALY | 2026-08-12 | pageviews | CRITICAL | Medium (0.723) | ru.wikipedia + mobile-web + automated |

## INC-20260812-PAGEVIEWS-RESIDUAL-ANOMALY

On 2026-08-12, pageviews showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified ru.wikipedia + mobile-web + automated as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review recent product, tracking, and campaign changes affecting pageviews.

### Suspected Root Causes
- full_segment: ru.wikipedia + mobile-web + automated (100.0% contribution)

### Recommended Actions
- Review recent product, tracking, and campaign changes affecting pageviews.
- Review pageviews drivers for full_segment = ru.wikipedia + mobile-web + automated; check recent releases, tracking changes, campaign mix, and operational issues.

### Supporting Metrics
- Actual value summary: `992742.0`
- Expected value summary: `1422326.428571`
- Percent variance summary: `-0.302029`
- Anomaly rows: `1`

## Limitations

- Live Wikimedia pageview data carries no ground-truth incident labels, so precision, recall and F1 cannot be computed for this track. Detector quality is measured on the labelled synthetic track instead.
- Traffic anomalies here are real but their causes are external and unverifiable - a spike may be a news event, a bot wave, or a Wikimedia infrastructure change. Root causes name the affected segment, not the reason.
- Recommended actions are rule based and should guide investigation, not prove causality.
