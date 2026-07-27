# KPI Incident Report

Generated at: `2026-07-27T15:00:48.538197+00:00`
Detector used: `residual_anomaly`
Incidents generated: **12**
Highest severity: **CRITICAL**

## Executive Summary

On 2026-05-18, latency_ms showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified North America + Desktop + Chrome as the dominant contributor, explaining 100.0% of excess latency. Recommended next step: Inspect regional latency, CDN routing, and browser-specific performance logs.

## Incident Table

| Incident ID | Date | KPI | Severity | Confidence | Top Root Cause |
|---|---:|---|---|---:|---|
| INC-20260518-LATENCY-MS-RESIDUAL-ANOMALY | 2026-05-18 | latency_ms | CRITICAL | High (0.835) | North America + Desktop + Chrome |
| INC-20260605-CONVERSION-RATE-RESIDUAL-ANOMALY | 2026-06-05 | conversion_rate | CRITICAL | High (0.835) | APAC + Mobile + Safari |
| INC-20260408-REVENUE-PER-SESSION-RESIDUAL-ANOMALY | 2026-04-08 | revenue_per_session | CRITICAL | Medium (0.730) | North America + Mobile + Chrome |
| INC-20260519-LATENCY-MS-RESIDUAL-ANOMALY | 2026-05-19 | latency_ms | CRITICAL | High (0.835) | North America + Desktop + Chrome |
| INC-20260520-LATENCY-MS-RESIDUAL-ANOMALY | 2026-05-20 | latency_ms | CRITICAL | High (0.835) | North America + Desktop + Chrome |
| INC-20260521-LATENCY-MS-RESIDUAL-ANOMALY | 2026-05-21 | latency_ms | CRITICAL | High (0.835) | North America + Desktop + Chrome |
| INC-20260522-LATENCY-MS-RESIDUAL-ANOMALY | 2026-05-22 | latency_ms | CRITICAL | High (0.835) | North America + Desktop + Chrome |
| INC-20260523-LATENCY-MS-RESIDUAL-ANOMALY | 2026-05-23 | latency_ms | CRITICAL | High (0.835) | North America + Desktop + Chrome |
| INC-20260524-LATENCY-MS-RESIDUAL-ANOMALY | 2026-05-24 | latency_ms | CRITICAL | High (0.835) | North America + Desktop + Chrome |
| INC-20260525-LATENCY-MS-RESIDUAL-ANOMALY | 2026-05-25 | latency_ms | CRITICAL | High (0.835) | North America + Desktop + Chrome |
| INC-20260606-CONVERSION-RATE-RESIDUAL-ANOMALY | 2026-06-06 | conversion_rate | CRITICAL | High (0.835) | APAC + Mobile + Safari |
| INC-20260607-CONVERSION-RATE-RESIDUAL-ANOMALY | 2026-06-07 | conversion_rate | CRITICAL | High (0.835) | APAC + Mobile + Safari |

## INC-20260518-LATENCY-MS-RESIDUAL-ANOMALY

On 2026-05-18, latency_ms showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified North America + Desktop + Chrome as the dominant contributor, explaining 100.0% of excess latency. Recommended next step: Inspect regional latency, CDN routing, and browser-specific performance logs.

### Suspected Root Causes
- region_device_browser: North America + Desktop + Chrome (100.0% contribution)
- full_segment: North America + Desktop + Chrome + Paid Search + Enterprise (11.8% contribution)
- full_segment: North America + Desktop + Chrome + Email + SMB (11.6% contribution)

### Recommended Actions
- Inspect regional latency, CDN routing, and browser-specific performance logs.
- Check backend response times and recent deployment windows.
- Compare Chrome performance against Safari and Firefox for the same region.

### Supporting Metrics
- Actual value summary: `343.280555`
- Expected value summary: `158.907229`
- Percent variance summary: `1.160715`
- Anomaly rows: `9`

## INC-20260605-CONVERSION-RATE-RESIDUAL-ANOMALY

On 2026-06-05, conversion_rate showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified APAC + Mobile + Safari as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review mobile Safari checkout/session flow.

### Suspected Root Causes
- region_device_browser: APAC + Mobile + Safari (100.0% contribution)
- full_segment: APAC + Mobile + Safari + Paid Search + Enterprise (14.0% contribution)
- full_segment: APAC + Mobile + Safari + Email + SMB (13.4% contribution)

### Recommended Actions
- Review mobile Safari checkout/session flow.
- Check recent frontend releases affecting mobile Safari users.
- Compare funnel steps for Mobile Safari against Chrome.

### Supporting Metrics
- Actual value summary: `0.051283`
- Expected value summary: `0.092398`
- Percent variance summary: `-0.44551`
- Anomaly rows: `9`

## INC-20260408-REVENUE-PER-SESSION-RESIDUAL-ANOMALY

On 2026-04-08, revenue_per_session showed a critical issue. The residual_anomaly detector flagged abnormal movement, and RCA identified North America + Mobile + Chrome as the dominant contributor, explaining 100.0% of measured degradation. Recommended next step: Review paid-search landing page quality for the affected segment.

### Suspected Root Causes
- region_device_browser: North America + Mobile + Chrome (100.0% contribution)
- full_segment: North America + Mobile + Chrome + Organic + SMB (53.6% contribution)
- full_segment: North America + Mobile + Chrome + Paid Search + SMB (46.4% contribution)

### Recommended Actions
- Review paid-search landing page quality for the affected segment.
- Check campaign targeting, landing page routing, and paid-search tracking.
- Compare paid-search revenue per session against Organic and Email traffic.

### Supporting Metrics
- Actual value summary: `0.317433`
- Expected value summary: `0.391253`
- Percent variance summary: `-0.190749`
- Anomaly rows: `2`

## Limitations

- Incident reports are generated from deterministic synthetic data.
- Recommended actions are rule based and should guide investigation, not prove causality.
