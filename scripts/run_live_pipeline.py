"""Operations track: run the tuned detector against live Wikimedia pageview data.

Fetches ~90 days of real public traffic, scores it with the same KPIMonitor /
AnomalyDetector / RootCauseAnalyzer used by the synthetic evaluation track, and writes a
report covering the most recent N days.

What this track does NOT do: compute precision, recall or F1. Live data has no labels.
Any accuracy claim about this detector comes from the synthetic track, which has injected
ground truth. Keeping that boundary explicit is the point of splitting the two.

Usage:
    python scripts/run_live_pipeline.py
    python scripts/run_live_pipeline.py --end-date 2026-07-20 --lookback-days 120
    python scripts/run_live_pipeline.py --offline    # re-score the last fetch, no network
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.anomaly_detection import AnomalyDetector
from src.core.incident_reporting import IncidentReporter
from src.core.kpi_monitoring import KPIMonitor
from src.core.live_ingestion import (
    LIVE_DIMENSION_SPECS,
    LIVE_DIMENSIONS,
    WikimediaPageviewsIngestor,
)
from src.core.root_cause import RootCauseAnalyzer

CONFIG_PATH = "config/live_monitoring_config.yaml"
LIVE_RAW_PATH = Path("data/live/raw/wikimedia_pageviews.csv")
LIVE_PROCESSED_DIR = Path("data/live/processed")
LIVE_REPORTS_DIR = Path("data/live/reports")


def _json_default(value):
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return str(value)


def run_live_pipeline(
    end_date: str | None = None,
    lookback_days: int | None = None,
    offline: bool = False,
) -> dict:
    ingestor = WikimediaPageviewsIngestor(config_path=CONFIG_PATH)
    report_window_days = int(
        ingestor.config.get("live_source", {}).get("report_window_days", 30)
    )

    if offline:
        if not LIVE_RAW_PATH.exists():
            raise FileNotFoundError(
                f"--offline needs a previous fetch at {LIVE_RAW_PATH}. Run without --offline first."
            )
        raw_df = pd.read_csv(LIVE_RAW_PATH)
        raw_df["date"] = pd.to_datetime(raw_df["date"])
        fetch_failures = []
    else:
        raw_df = ingestor.fetch(end_date=end_date, lookback_days=lookback_days)
        ingestor.write_raw(raw_df, LIVE_RAW_PATH)
        fetch_failures = getattr(ingestor, "last_failures", [])

    # --- monitoring -------------------------------------------------------------
    monitor = KPIMonitor(config_path=CONFIG_PATH, dimensions=LIVE_DIMENSIONS)
    monitoring = monitor.build_monitoring_table(raw_df)

    LIVE_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    LIVE_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    monitoring.to_csv(LIVE_PROCESSED_DIR / "live_monitoring_table.csv", index=False)

    # --- detection --------------------------------------------------------------
    detector = AnomalyDetector(config_path=CONFIG_PATH, dimensions=LIVE_DIMENSIONS)
    anomaly_results = detector.build_anomaly_results(monitoring, raw_df)
    anomaly_results.to_csv(LIVE_PROCESSED_DIR / "live_anomaly_results.csv", index=False)

    # Report only the recent window. Earlier days exist purely to warm the 28-day
    # baseline and would otherwise flood the report with stale findings.
    max_date = pd.to_datetime(anomaly_results["date"]).max()
    window_start = max_date - pd.Timedelta(days=report_window_days - 1)
    recent = anomaly_results[pd.to_datetime(anomaly_results["date"]) >= window_start].copy()

    # --- root cause -------------------------------------------------------------
    analyzer = RootCauseAnalyzer(
        config_path=CONFIG_PATH,
        dimension_specs=LIVE_DIMENSION_SPECS,
    )
    contribution_table = analyzer.build_contribution_table(recent)
    contribution_table.to_csv(
        LIVE_PROCESSED_DIR / "live_rca_contribution_table.csv", index=False
    )
    rca_summary, _ = analyzer.write_outputs(
        contribution_table,
        summary_path=LIVE_REPORTS_DIR / "live_root_cause_summary.json",
        top_causes_path=LIVE_REPORTS_DIR / "live_top_root_causes.csv",
        total_anomalies_analyzed=analyzer.count_rca_candidates(recent),
        candidate_summary=analyzer.summarize_candidate_filter(recent),
    )

    # --- coverage / run metadata -------------------------------------------------
    scoreable = anomaly_results["z_score"].notna().sum()
    run_summary = {
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "track": "live_operations",
        "source": "Wikimedia Pageviews API",
        "date_min": str(pd.to_datetime(anomaly_results["date"]).min().date()),
        "date_max": str(max_date.date()),
        "report_window_days": report_window_days,
        "report_window_start": str(window_start.date()),
        "total_rows_fetched": int(len(raw_df)),
        "series_count": int(raw_df.groupby(LIVE_DIMENSIONS[1:]).ngroups),
        "rows_scored": int(scoreable),
        "rows_unscored_baseline_warmup": int(len(anomaly_results) - scoreable),
        "rows_in_report_window": int(len(recent)),
        "residual_model_used": detector.residual_model_used,
        "fetch_failures": fetch_failures,
        "anomalies_in_window": {
            "zscore": int(recent["zscore_anomaly"].sum()),
            "residual": int(recent["residual_anomaly"].sum()),
            "combined": int(recent["combined_anomaly"].sum()),
        },
        "labels_available": False,
        "accuracy_note": (
            "No ground-truth labels exist for live traffic, so precision/recall/F1 are "
            "not computed here. Detector accuracy is measured on the synthetic track."
        ),
    }
    # --- live data quality --------------------------------------------------------
    # The synthetic schema contract does not apply to this source, so quality here is
    # measured as fetch coverage: how much of the requested series x day grid actually
    # arrived. A partial API response should visibly lower incident confidence.
    expected_series = (
        len(ingestor.projects) * len(ingestor.access_types) * len(ingestor.agent_types)
    )
    observed_days = int(pd.to_datetime(raw_df["date"]).dt.date.nunique())
    expected_cells = expected_series * observed_days
    coverage = (len(raw_df) / expected_cells) if expected_cells else 0.0
    live_quality = {
        "health_score": round(coverage * 100, 2),
        "status": "PASS" if coverage >= 0.98 and not fetch_failures else "FAIL",
        "expected_series": expected_series,
        "observed_series": int(raw_df.groupby(LIVE_DIMENSIONS[1:]).ngroups),
        "observed_days": observed_days,
        "coverage_pct": round(coverage * 100, 2),
        "fetch_failures": fetch_failures,
    }
    with open(LIVE_REPORTS_DIR / "live_data_quality.json", "w") as f:
        json.dump(live_quality, f, indent=2, default=_json_default)
    run_summary["live_data_quality"] = live_quality

    # --- incident report ---------------------------------------------------------
    # Detector F1 is carried over from the labelled synthetic track. It is an input to the
    # confidence score because it describes the detector, not this dataset - there is no
    # way to compute F1 here. The provenance is recorded so the number is never mistaken
    # for a measurement taken on live data.
    synthetic_comparison_path = Path("data/reports/model_comparison.json")
    model_comparison = {
        "best_detector": "residual_anomaly",
        "note": "Detector selected and scored on the labelled synthetic track; not re-scored on live data.",
    }
    if synthetic_comparison_path.exists():
        synthetic = json.loads(synthetic_comparison_path.read_text())
        model_comparison["best_detector_f1_score"] = synthetic.get("best_detector_f1_score")
        model_comparison["f1_source"] = "synthetic_evaluation_track"

    with open(LIVE_REPORTS_DIR / "live_run_summary.json", "w") as f:
        json.dump(run_summary, f, indent=2, default=_json_default)

    reporter = IncidentReporter(config_path=CONFIG_PATH)
    incident_payload = reporter.generate_reports(
        recent,
        contribution_table,
        model_comparison=model_comparison,
        root_cause_summary=rca_summary,
        data_quality_report=live_quality,
        monitoring_summary={"total_monitoring_rows": int(len(monitoring))},
        json_path=LIVE_REPORTS_DIR / "live_latest_incident.json",
        markdown_path=LIVE_REPORTS_DIR / "live_latest_incident.md",
        html_path=LIVE_REPORTS_DIR / "live_latest_incident.html",
        history_path=LIVE_REPORTS_DIR / "live_incident_history.csv",
    )

    print(f"Live rows fetched      : {run_summary['total_rows_fetched']}")
    print(f"Series monitored       : {run_summary['series_count']}")
    print(f"Date range             : {run_summary['date_min']} -> {run_summary['date_max']}")
    print(f"Rows scored            : {run_summary['rows_scored']}")
    print(f"Report window          : last {report_window_days} days")
    print(f"Anomalies (combined)   : {run_summary['anomalies_in_window']['combined']}")
    print(f"Incidents generated    : {incident_payload['incidents_generated']}")
    if fetch_failures:
        print(f"Partial coverage       : {len(fetch_failures)} series failed to fetch")

    return run_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the live operations monitoring track.")
    parser.add_argument("--end-date", default=None, help="Last day to fetch (YYYY-MM-DD). Defaults to yesterday.")
    parser.add_argument("--lookback-days", type=int, default=None, help="Days of history to fetch.")
    parser.add_argument("--offline", action="store_true", help="Re-score the last fetch without calling the API.")
    args = parser.parse_args()

    run_live_pipeline(
        end_date=args.end_date,
        lookback_days=args.lookback_days,
        offline=args.offline,
    )


if __name__ == "__main__":
    main()
