# TASKS — KPI Reliability & Diagnostic Engine (Flagship #2)

Legend: `[AGENT]` = Claude Code can complete and verify. `[HUMAN]` = needs credentials, GUI
tooling, or Kartz's accounts.

This flagship is a **packaging upgrade of working code, not a rebuild.** The detection and
RCA engine already worked; the gap was that the result was not told, the headline numbers
were not re-verified, and the repository had started to rot on a clock.

Last loop update: 2026-07-25.

---

## Verified baseline (established this session)

- Full pipeline re-run from scratch (`python3 scripts/run_pipeline.py --regenerate`)
  reproduced **every prior artifact byte-identically**: raw data, validated data, monitoring
  table, anomaly results, RCA contribution table, and model evaluation. Only `run_timestamp`
  fields changed. The project is genuinely deterministic.
- Detector evaluation, over 121,500 rows with 342 labelled incident rows:

  | Detector | Precision | Recall | F1 | TP | FP | FN |
  | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
  | `monitoring_threshold` | 0.1036 | 1.0000 | 0.1878 | 342 | 2,958 | 0 |
  | `rolling_zscore` | 0.1033 | 0.2778 | 0.1506 | 95 | 825 | 247 |
  | `ml_residual` | 0.3779 | 1.0000 | 0.5485 | 342 | 563 | 0 |
  | `combined` | 0.2015 | 1.0000 | 0.3355 | 342 | 1,355 | 0 |

- **The brief's headline numbers check out.** 2,958 → 563 false positives is a **80.97%**
  reduction; F1 0.1878 → 0.5485; recall held at 1.00. These were re-derived, not carried
  forward.
- Test suite: **60 passed** (was 59 passed / 1 failed — see B1).

---

## A. Foundation

- [x] **A1 [AGENT]** Add `CLAUDE.md` and `TASKS.md`. *done = both present; CLAUDE.md carries the flagship-2 working notes.*
- [x] **A2 [AGENT]** Re-derive every headline metric from a real run rather than trusting prior notes. *done = table above, reproduced byte-identically.*

## B. Correctness — issues found and fixed this session

- [x] **B1 [AGENT]** **Fix the time bomb.** `scripts/generate_raw_data.py` hardcoded incident windows as absolute dates while the data quality layer checks freshness against *today* with a 14-day threshold. The shipped dataset ends 2026-06-30, so from ~2026-07-14 the quality gate returned `FAIL` and `test_valid_generated_dataset_passes_quality_validation` failed on every clone. *done = incident windows are now day offsets from the dataset end date; `--end-date` added to the pipeline; the quality test fixture anchors to today. **Verified byte-identical output on the default end date**, and `--regenerate --end-date $(date +%F)` yields 121,500 rows, the same 342 labelled incident rows, and a `PASS` at 100/100. Suite now 60/60.*
- [x] **B2 [AGENT]** **Fix a false claim in the README.** It stated the latest run "passed all validation checks and achieved a data quality score of 100/100". The actual committed run scores **90/100 with status `FAIL`** on the freshness check. *done = replaced with the real per-check result plus the reason the shipped extract is stale by construction and the command to regenerate it fresh.*
- [x] **B3 [AGENT]** Add the `--end-date` flag that the new README text referenced. *done = flag added to `run_pipeline.py` with a guard that errors if used without `--regenerate`; both paths executed and verified.*

## C. Packaging — the actual deliverable

- [x] **C1 [AGENT]** Before/after comparison table in the README. *done = "Headline Result" section leading the README with the full confusion-matrix comparison, the analyst-workload framing (3,300 alerts → 905 for the same 342 incidents), and the reproduction command.*
- [x] **C2 [AGENT]** Write `docs/decisions.md` — Decisions & tradeoffs. *done = 6 decisions with Context / Options / Chosen / Tradeoff, including why the rolling Z-score was **rejected** despite cutting alert volume 72%.*
- [x] **C3 [AGENT]** Diagram the detection → RCA flow. *done = Mermaid flowchart in `docs/decisions.md`, showing all three detectors converging on evaluation, the rejected branch, and RCA as the step that makes the system diagnostic.*
- [x] **C4 [AGENT]** Streamlit layout spec. *done = `dashboards/layout_spec.md`, six pages documented against the actual implementation, each with the artifacts it reads and the question it answers.*
- [x] **C5 [AGENT]** Grounded resume bullets in `docs/resume_bullets.md`. *done = 7 bullets with a source table mapping each figure to its artifact, framing notes on the synthetic data / NumPy fallback / 37.79% precision, and a "Not yet true" table covering the un-run warehouse layer and missing screenshots.*

## D. Human steps

- [ ] **D1 [HUMAN — decision]** **Should the committed dataset be re-anchored to a current date?** Currently pinned to 2026-06-30 so every published figure stays exactly reproducible, at the cost of the repo shipping a dataset that fails its own freshness gate. Re-anchoring makes the quality page green but **moves the residual model's train/test split**: `ml_residual` false positives go 563 → 599 and F1 0.5485 → 0.5331 (the static-threshold baseline stays at 2,958, so the ~81% headline is unaffected — it becomes 79.75%). *done = Kartz picks one; if re-anchored, every figure in the README, `docs/decisions.md`, and the resume bullets must be updated together.*
- [ ] **D2 [HUMAN]** Re-run and capture the six dashboard screenshots into `dashboards/screenshots/` per `dashboards/layout_spec.md`. Capturing the Anomaly Timeline twice — once under `monitoring_threshold`, once under `residual_anomaly` — is the single most valuable image in the set.
- [ ] **D3 [HUMAN]** Load the warehouse and run dbt. The agent did not run the PostgreSQL/dbt layer this session; `scripts/load_postgres.py` and `dbt/` were not executed, so no dbt test count is claimed. *done = `dbt build` PASS count recorded here.*
- [ ] **D4 [HUMAN]** Push and pin. Note the remote is **`github.com/Kartz82/kpi-anomaly-diagnostics`**, while the local directory is `data-reliability-kpi-monitoring` — confirm which name should be the public one before pinning.
