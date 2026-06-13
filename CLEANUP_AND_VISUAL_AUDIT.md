# Cleanup and Visual Audit

Date: 2026-06-13

Scope: local project repository only. No portfolio repository was inspected, referenced, or modified.

## Repo Structure Summary

- `config/`: YAML monitoring configuration for simulation, KPI, and segment settings.
- `data/reports/`: generated diagnostic outputs for local review, including JSON, text, and interactive Plotly HTML reports.
- `data/raw/`: empty data placeholder; ignored by `.gitignore`.
- `data/warehouse/`: empty data placeholder; ignored by `.gitignore`.
- `reports/figures/`: generated static PNG report figures.
- `sql/`: SQL schema and example diagnostic queries.
- `src/core/`: Python implementation for ingestion, data quality validation, anomaly detection, root-cause analysis, reporting, and utilities.
- `main.py`: end-to-end pipeline entry point that loads config, simulates data, validates quality, detects anomalies, performs root-cause analysis, and exports reports.
- `tests/`: empty placeholder folder.
- `notebooks/`: empty placeholder folder.

## Cleanup Performed

Deleted:

- `.DS_Store`
- `reports/.DS_Store`
- `src/core/__pycache__/`

Changed:

- `.gitignore`
  - Added or confirmed prevention rules for `.DS_Store`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ipynb_checkpoints/`, `.env`, `venv/`, and `.venv/`.
  - Kept existing ignore rules for generated/raw data placeholders and existing Python patterns.

Created:

- `CLEANUP_AND_VISUAL_AUDIT.md`

## Cleanup Candidates Not Deleted

These items look possibly unnecessary because they are empty, but they were not deleted because they may be intentional project placeholders:

- `tests/`: empty; keep if future test coverage is planned.
- `notebooks/`: empty; keep if exploratory analysis notebooks are planned.
- `data/raw/`: empty; ignored by `.gitignore`; likely intended for local raw inputs.
- `data/warehouse/`: empty; ignored by `.gitignore`; likely intended for local intermediate or modeled data.

No generated PNG reports, CSVs, JSON outputs, Python scripts, SQL files, source folders, or report folders were deleted.

## Current Visualization and Export Files

The Python file that generates PNG reports is `src/core/reporting.py`.

The report generation flow is:

- `main.py` builds the pipeline inputs and calls `ReportGenerator`.
- `ReportGenerator.generate_report()` prints a console diagnostic and writes `data/reports/latest_diagnostic.json`.
- `ReportGenerator.generate_visualizations()` builds three interactive HTML charts and four static PNGs.
- `ReportGenerator.generate_incident_center()` builds the incident center HTML and PNG.

Current PNG-writing functions:

- `_write_static_chart(fig, file_path)`: writes PNGs with `fig.write_image(file_path, scale=2)`.
- `_write_interactive_chart(fig, file_path)`: writes HTML with Plotly CDN.

Current report-building functions:

- `_build_kpi_timeseries()`: KPI trend time-series chart.
- `_build_anomaly_zscore()`: max absolute anomaly z-score time-series chart with alert threshold.
- `_build_segment_root_cause()`: horizontal segment-level root-cause bar chart.
- `_build_incident_summary()`: KPI incident summary with three indicator values and context annotations.
- `_build_incident_center()`: multi-KPI incident table.

Current PNGs:

- `reports/figures/kpi_timeseries.png`
- `reports/figures/anomaly_zscore.png`
- `reports/figures/segment_root_cause.png`
- `reports/figures/incident_summary.png`
- `reports/figures/incident_center.png`

Combined or stacked PNGs:

- None are file-level stacked PNGs or PIL-composited images.
- `incident_summary.png` is a multi-panel Plotly figure made from three `go.Indicator` traces plus annotations.
- `incident_center.png` is a Plotly table figure, not an image stack.

Single-chart exports:

- `kpi_timeseries.png`: single Plotly line chart.
- `anomaly_zscore.png`: single Plotly line chart with threshold line.
- `segment_root_cause.png`: single Plotly horizontal bar chart.

## Current Report PNG Inventory

| Filename | Folder | Likely purpose | Portfolio-ready | Stacked/composite | Recommendation |
|---|---|---|---|---|---|
| `incident_center.png` | `reports/figures/` | Multi-KPI incident triage table for conversion rate, CTR, and latency | Partial | Composite Plotly table, not stacked image | Keep now; regenerate for portfolio |
| `incident_summary.png` | `reports/figures/` | Executive summary for the monitored conversion-rate incident | Partial | Composite Plotly indicator figure | Keep now; regenerate for portfolio |
| `segment_root_cause.png` | `reports/figures/` | Ranked segment-level root-cause evidence by z-score | Partial | Single bar chart | Keep now; regenerate for portfolio |
| `anomaly_zscore.png` | `reports/figures/` | Daily max absolute z-score and alert threshold | Partial | Single line chart | Keep now; regenerate for portfolio |
| `kpi_timeseries.png` | `reports/figures/` | Daily conversion-rate trend | Partial | Single line chart | Keep now; regenerate or deprioritize |

## Chart Generation Logic

KPI summary:

- `main.py::build_incident_row()` formats per-KPI incident rows for the incident center.
- `ReportGenerator._build_incident_summary()` creates the monitored KPI summary figure.
- `ReportGenerator._build_incident_center()` creates the multi-KPI incident table.

Time-series charts:

- `ReportGenerator._build_kpi_timeseries()` aggregates by date and renders a Plotly Express line chart.
- Aggregation is `mean` for metrics ending in `_rate` and for `ctr` and `latency_ms`; otherwise it uses `sum`.

Anomaly and z-score charts:

- `ReportGenerator._build_anomaly_zscore()` groups by date, calculates daily max absolute z-score, and renders a Plotly Graph Objects line chart with a red dashed alert threshold at `2.0`.
- The underlying z-score columns are generated upstream by `src/core/anomaly_detection.py`.

Root-cause charts:

- `ReportGenerator._build_segment_root_cause()` reads `ranked_anomalies` from root-cause output and renders a horizontal Plotly Express bar chart by segment and z-score.
- If there are no ranked anomalies, it renders a no-anomalies annotation instead.

Incident-center and incident-summary outputs:

- `main.py` loops through all configured KPIs, detects anomalies for each, runs root-cause analysis, and converts each result into an incident row.
- `ReportGenerator.generate_incident_center()` writes `data/reports/incident_center.html` and `reports/figures/incident_center.png`.
- `ReportGenerator.generate_visualizations()` writes `reports/figures/incident_summary.png` for the monitored KPI.

Rendering libraries:

- Plotly Express: KPI time-series line chart and segment root-cause bar chart.
- Plotly Graph Objects: anomaly z-score line chart, incident summary indicators, incident center table.
- Kaleido/Plotly image export: static PNG generation through `fig.write_image()`.
- Matplotlib: not used for current report PNG generation.
- Seaborn: not used.
- PIL compositing: not used.

## Styling Audit

`incident_center.png`:

- Background/style: white Plotly background with dark table header and pale severity cell fills.
- Dark portfolio match: not yet; it is light-themed and would need dark-compatible layout/colors.
- Text readability: readable at full size; table text is dense but acceptable.
- Bar widths: not applicable.
- Color polish: functional, but severity colors are basic.
- Needs v2/professional redesign: yes.

`incident_summary.png`:

- Background/style: white Plotly indicator layout with large navy values and large whitespace.
- Dark portfolio match: not yet.
- Text readability: readable, but spacing feels oversized and presentation-like rather than dashboard-polished.
- Bar widths: not applicable.
- Color polish: minimal; mostly monochrome navy on white.
- Needs v2/professional redesign: yes.

`segment_root_cause.png`:

- Background/style: white Plotly chart, horizontal bars, default continuous color scale.
- Dark portfolio match: not yet.
- Text readability: readable, including segment labels and axis labels.
- Bar widths: acceptable but visually heavy; spacing and color scale could be more refined.
- Color polish: default Plotly colors look technical rather than intentionally branded.
- Needs v2/professional redesign: yes.

`anomaly_zscore.png`:

- Background/style: white Plotly line chart with pale grid, blue line/markers, red dashed threshold.
- Dark portfolio match: not yet.
- Text readability: readable.
- Bar widths: not applicable.
- Color polish: clear but basic; threshold annotation placement is functional.
- Needs v2/professional redesign: yes, especially if used as a portfolio hero/evidence chart.

`kpi_timeseries.png`:

- Background/style: white Plotly line chart with pale grid and blue line/markers.
- Dark portfolio match: not yet.
- Text readability: readable.
- Bar widths: not applicable.
- Color polish: basic default chart style.
- Needs v2/professional redesign: optional; useful supporting chart but not the strongest portfolio artifact.

## Best Candidates for Portfolio

Top 3 professional PNGs to regenerate later:

1. Incident Center
2. KPI Summary
3. Root Cause Analysis

Secondary candidate:

- Anomaly Threshold Timeline

## Recommended New PNG Names

Suggested future regenerated PNG paths:

- `reports/incident_center_professional.png`
- `reports/kpi_summary_professional.png`
- `reports/root_cause_analysis_professional.png`
- `reports/anomaly_threshold_timeline_professional.png`
- `reports/conversion_rate_trend_professional.png`

These names avoid raw technical labels, do not use `v2`, and are clean enough for portfolio-facing assets.

## Risks Before Regenerating Charts

- `main.py` currently calls the reporting methods as part of the full pipeline. Running it regenerates JSON, HTML, and all static PNG report outputs together.
- The static PNG export depends on Plotly image export through Kaleido. Environment or package-version changes can break `fig.write_image()`.
- Report filenames are hardcoded in `ReportGenerator.generate_visualizations()` and `ReportGenerator.generate_incident_center()`. Renaming outputs in code may require README updates.
- `README.md` embeds the current PNG paths under `reports/figures/`; moving or replacing files could break README image previews.
- `incident_center.png` depends on the incident-row schema produced by `main.py::build_incident_row()`. Changing row keys or names can break the table.
- `incident_summary.png` assumes `primary_offender` includes `segment`, `z_score`, `actual_value`, `rolling_mean`, and date information when an anomaly is detected.
- The chart content is coupled to the configured KPI order: `main.py` uses the first configured KPI as the monitored KPI for the main visualizations.
- Styling-only chart work should avoid modifying source data, SQL, anomaly detection, root-cause ranking, metric aggregation, or report calculations.

## Completion Notes

Files changed:

- `.gitignore`
- `CLEANUP_AND_VISUAL_AUDIT.md`

Files deleted:

- `.DS_Store`
- `reports/.DS_Store`
- `src/core/__pycache__/`

Report saved at:

- `CLEANUP_AND_VISUAL_AUDIT.md`
