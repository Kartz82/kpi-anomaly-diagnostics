# Resume Bullets — KPI Reliability & Diagnostic Engine

Every number below was re-derived from a real pipeline run on 2026-07-25, not carried
forward from prior notes. Reproduce them with:

```bash
python3 scripts/run_pipeline.py --regenerate
cat data/reports/model_evaluation.csv
```

---

## Ready to use — every figure verified

> Replaced static-threshold KPI monitoring with **residual-based anomaly detection**,
> cutting false positives **from 2,958 to 563 (−81%)** and raising F1 from **0.1878 to
> 0.5485** across 121,500 observations — while holding recall at **100%**, so no incident
> was traded away for the precision gain.

> Built a contribution-based root-cause layer that decomposes each KPI movement across five
> dimensions (region, device, browser, channel, segment) and ranks the combinations driving
> it, turning "conversion rate dropped" into a named segment to investigate.

> Evaluated three detection methods against labelled ground truth and **rejected the one
> with the best-looking alert reduction** — a rolling Z-score cut alerts 72% but missed 247
> of 342 incidents (recall 27.8%), scoring below the baseline it was meant to replace.

> Cut analyst triage load from **3,300 alerts to 905** for the same 342 real incidents,
> improving the false-alarm ratio from roughly 9 per incident to under 2.

> Engineered a fully deterministic pipeline — data generation, quality validation,
> monitoring, detection, RCA, and incident reporting — that reproduces **byte-identical
> outputs** across clean runs, making every published metric independently verifiable.

> Built a 10-check data quality gate (schema, types, accepted values, nulls, duplicates,
> freshness, completeness, volume, numeric ranges) with an explainable 0-100 health score
> that blocks certification on failure rather than warning silently.

> Diagnosed and fixed a latent defect where hardcoded incident dates caused the project's
> own quality gate and test suite to fail two weeks after the pinned dataset date;
> re-expressed the injected incident windows as offsets from the dataset end date and
> **proved the refactor output-neutral by byte-comparing all six pipeline artifacts.**

### Where each figure comes from

| Figure | Source |
| :--- | :--- |
| 2,958 → 563 false positives; 80.97% reduction | `data/reports/model_evaluation.csv`, rows `monitoring_threshold` and `ml_residual` |
| F1 0.187809 → 0.548516; recall 1.0 both | same file |
| Rolling Z-score: 95 TP, 247 FN, recall 0.2778, F1 0.1506 | same file |
| 121,500 rows / 150 days / 5 KPIs / 5 dimensions | `data/raw/kpi_daily_metrics.csv`, `scripts/generate_raw_data.py` |
| 342 labelled incident rows | `support` column, same evaluation file |
| 3,300 → 905 alerts | TP + FP per detector |
| Byte-identical reproduction | full `--regenerate` re-run diffed against prior artifacts; only `run_timestamp` changed |
| 60 passing tests | `python3 -m pytest -q` |
| Quality gate 9/10 checks, 90/100, `FAIL` on freshness | `data/reports/data_quality_report.json` |

---

## Framing notes — say these, they are strengths

- **The data is synthetic, and lead with that.** Precision/recall/F1 are only meaningful
  against ground truth; no public KPI dataset carries reliable incident labels. Controlled
  labels are what make the 81% a measurement rather than an assertion. Incident labels are
  used only for evaluation, never as model features — enforced and recorded in
  `model_comparison.json`.
- **The residual model is NumPy ridge regression, not XGBoost.** XGBoost and scikit-learn
  could not be imported locally due to native SciPy dependency failures. The code attempts
  them first and records which path ran. A reproducible ridge result beats an
  irreproducible boosted one, and 0.5485 F1 is therefore a floor.
- **Precision is 37.79%, not 90%.** Roughly three in five alerts are still not incidents.
  Saying so is more credible than implying near-perfection, and the reason is a deliberate
  design choice: recall is pinned at 100% because a missed revenue or latency incident costs
  far more than a minute of triage.

## Not yet true — do not use until run

| Claim | Blocked on | Becomes true when |
| :--- | :--- | :--- |
| "Built a PostgreSQL + dbt warehouse layer with N passing tests" | The warehouse layer was **not executed** in this session | `scripts/load_postgres.py` and `dbt build` run and a real test count is recorded (`TASKS.md` D3) |
| Any dashboard screenshot claim | Screenshots not captured | The six captures in `dashboards/layout_spec.md` exist (`TASKS.md` D2) |

## Pinned repository description

> Automated KPI monitoring and diagnostic engine: residual-based anomaly detection cut false
> positives 81% (2,958 → 563) at 100% recall versus static thresholds, with contribution-based
> root-cause analysis across five dimensions, a 10-check data quality gate, and a fully
> deterministic, byte-reproducible pipeline.
