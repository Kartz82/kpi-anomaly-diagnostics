# Dashboard Layer

This directory contains the Streamlit executive dashboard for the KPI Reliability & Diagnostic Engine.

## Local Run

```bash
streamlit run dashboards/streamlit_app.py
```

The dashboard reads local CSV and JSON outputs by default. PostgreSQL is not
required for normal dashboard usage.

PostgreSQL is not required for normal dashboard usage.

## Pages

- Executive Overview
- KPI Health
- Anomaly Timeline
- Root Cause Explorer
- Data Quality
- Incident Center

## Inputs

- `data/processed/kpi_monitoring_table.csv`
- `data/processed/anomaly_results.csv`
- `data/processed/rca_contribution_table.csv`
- `data/reports/data_quality_report.json`
- `data/reports/kpi_monitoring_summary.json`
- `data/reports/model_evaluation.csv`
- `data/reports/model_comparison.json`
- `data/reports/root_cause_summary.json`
- `data/reports/latest_incident.json`
- `data/reports/incident_history.csv`

## Notes

- The dashboard is intentionally local-file first for reproducibility.
- Optional warehouse/dbt exploration can be added later, but is not required.
- Final portfolio polish, including richer visual assets, remains a follow-up task.
