# Streamlit Dashboard Layout Specification

This documents the layout implemented in `dashboards/streamlit_app.py` — six pages behind a
sidebar radio selector, each answering one question and reading from pipeline artifacts
rather than recomputing anything.

Run it with:

```bash
streamlit run dashboards/streamlit_app.py
```

The app reads the CSV and JSON outputs in `data/processed/` and `data/reports/`. Run the
pipeline first, or every page will render empty:

```bash
python3 scripts/run_pipeline.py --regenerate
```

---

## Global structure

| Element | Behaviour |
| :--- | :--- |
| Title | "KPI Reliability & Diagnostic Engine", persistent across pages |
| Navigation | `st.sidebar.radio` over the six pages, Executive Overview first |
| Filters | Page-scoped, rendered into the sidebar below navigation |
| Data loading | Cached loaders per artifact; a missing file degrades to an empty frame instead of raising |

**Loading is deliberately fault-tolerant.** `_safe_read_csv` returns an empty DataFrame when
an artifact is absent, so a partially-run pipeline renders a degraded dashboard rather than
a stack trace. A dashboard that crashes on missing input is useless during the exact
incident it exists to explain.

---

## Page 1 — Executive Overview

**Question:** is the platform healthy right now, and if not, what is worst?

| Region | Content |
| :--- | :--- |
| Metric cards (6 columns) | KPIs Monitored · Date Range · Data Health · Anomalies · Incidents · Best Detector (with its F1) |
| KPI Health Summary | Table per KPI: threshold breaches, mean percent variance, max absolute percent variance, sorted by breaches descending |
| Latest / Top Incident | Executive summary text for the highest-confidence incident, captioned with severity and confidence label |
| Monitoring Summary | Table of warning count, critical count, threshold breach count, highest severity |

Guard: if the monitoring or anomaly artifacts are empty the page renders a warning and
returns rather than rendering broken cards.

Reads: `kpi_monitoring_table.csv`, `anomaly_results.csv`, `data_quality_report.json`,
`model_comparison.json`, `kpi_monitoring_summary.json`, `latest_incident.json`.

Putting the **Best Detector card, with its F1, on the executive page** is deliberate: the
headline of this project is that detection quality was measured, not assumed, and that
belongs where a stakeholder lands first.

## Page 2 — KPI Health

**Question:** how is one KPI behaving, in one slice, over time?

Sidebar filters: KPI selector, date-range slider, and per-dimension multiselects (region,
device type, browser, channel, business segment).

Primary visual: actual vs expected over time, with the monitoring status band. This is the
page where "expected" becomes visible as a line rather than an abstraction — the single most
useful view for explaining residual detection to a stakeholder.

Reads: `kpi_monitoring_table.csv`.

## Page 3 — Anomaly Timeline

**Question:** which detector fired, when, and do they agree?

Sidebar filter: detector selector (`monitoring_threshold`, `rolling_zscore`,
`residual_anomaly`, `combined`).

Switching detectors on the same timeline is the argument for residual detection made
visually: the threshold detector's markers carpet the chart, the residual detector's cluster
on the injected incident windows.

Reads: `anomaly_results.csv`.

## Page 4 — Root Cause Explorer

**Question:** which dimension combination accounts for the movement?

Sidebar filters: KPI, analysis date, dimension type, detector.

Primary visual: contribution ranking — dimension combinations sorted by share of the excess
movement, with the contribution share on the bar. This is the page that makes the project
diagnostic rather than descriptive.

Reads: `rca_contribution_table.csv`, `top_root_causes.csv`.

## Page 5 — Data Quality

**Question:** can the numbers on the other five pages be trusted?

Shows the health score, per-check pass/fail with each check's score, and the issue list.

**This page must be able to show a failure, and currently does.** The committed dataset ends
2026-06-30 and fails the 14-day freshness check, so the page renders 9 of 10 checks passing
at a 90/100 score with `FAIL` status. Regenerate with `--end-date $(date +%F)` to see the
100/100 `PASS` state. A quality page that can only ever render green is decoration.

Reads: `data_quality_report.json`.

## Page 6 — Incident Center

**Question:** what happened, how confident are we, and what should someone do?

Sidebar filters: severity multiselect, confidence multiselect. Main area: incident list plus
a detail selector showing the full incident record — severity, confidence, contributing
segment, and suggested investigation.

Reads: `incident_history.csv`, `latest_incident.json`.

---

## Screenshots to capture

Into `dashboards/screenshots/`:

| File | Content |
| :--- | :--- |
| `executive_overview.png` | Page 1, default state |
| `kpi_health.png` | Page 2, conversion_rate with the expected-vs-actual gap visible |
| `anomaly_timeline.png` | Page 3, `residual_anomaly` selected |
| `root_cause_explorer.png` | Page 4, showing a dominant contributor |
| `data_quality.png` | Page 5, showing the freshness check state |
| `incident_center.png` | Page 6, with an incident detail expanded |

For the anomaly timeline, capturing the same view under `monitoring_threshold` and under
`residual_anomaly` makes the 2,958 → 563 false-positive reduction legible at a glance —
worth more than any single screenshot in the set.
