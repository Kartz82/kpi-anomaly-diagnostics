from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.generate_raw_data import generate_kpi_data
from src.core.anomaly_detection import AnomalyDetector
from src.core.data_quality import DataQualityValidator
from src.core.ingestion import DataIngestor
from src.core.incident_reporting import IncidentReporter
from src.core.kpi_monitoring import KPIMonitor
from src.core.model_evaluation import ModelEvaluator
from src.core.root_cause import RootCauseAnalyzer


RAW_PATH = ROOT_DIR / "data/raw/kpi_daily_metrics.csv"
PROCESSED_PATH = ROOT_DIR / "data/processed/kpi_validated.csv"
REPORT_PATH = ROOT_DIR / "data/reports/data_quality_report.json"
SCHEMA_CONTRACT_PATH = ROOT_DIR / "config/schema_contract.yaml"
MONITORING_CONFIG_PATH = ROOT_DIR / "config/monitoring_config.yaml"
MONITORING_TABLE_PATH = ROOT_DIR / "data/processed/kpi_monitoring_table.csv"
MONITORING_SUMMARY_PATH = ROOT_DIR / "data/reports/kpi_monitoring_summary.json"
ANOMALY_RESULTS_PATH = ROOT_DIR / "data/processed/anomaly_results.csv"
MODEL_EVALUATION_PATH = ROOT_DIR / "data/reports/model_evaluation.csv"
MODEL_COMPARISON_PATH = ROOT_DIR / "data/reports/model_comparison.json"
RCA_TABLE_PATH = ROOT_DIR / "data/processed/rca_contribution_table.csv"
ROOT_CAUSE_SUMMARY_PATH = ROOT_DIR / "data/reports/root_cause_summary.json"
TOP_ROOT_CAUSES_PATH = ROOT_DIR / "data/reports/top_root_causes.csv"
LATEST_INCIDENT_JSON_PATH = ROOT_DIR / "data/reports/latest_incident.json"
LATEST_INCIDENT_MD_PATH = ROOT_DIR / "data/reports/latest_incident.md"
LATEST_INCIDENT_HTML_PATH = ROOT_DIR / "data/reports/latest_incident.html"
INCIDENT_HISTORY_PATH = ROOT_DIR / "data/reports/incident_history.csv"


def _json_default(value):
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def run_phase_1_pipeline(regenerate: bool = False, end_date: str | None = None) -> dict:
    if regenerate or not RAW_PATH.exists():
        # end_date=None keeps the generator's pinned default (2026-06-30), which is what
        # every published metric was produced from. Passing an explicit end date
        # re-anchors the dataset - incident windows are offsets from the end date, so the
        # labelled ground truth moves with it and the evaluation stays valid.
        generate_kwargs = {"output_path": RAW_PATH}
        if end_date:
            generate_kwargs["end_date"] = end_date
        raw_df = generate_kpi_data(**generate_kwargs)
        raw_action = "generated"
    else:
        raw_df = None
        raw_action = "read"

    ingestor = DataIngestor(schema_contract_path=str(SCHEMA_CONTRACT_PATH))
    df = ingestor.load_raw_data(str(RAW_PATH))

    validator = DataQualityValidator(str(SCHEMA_CONTRACT_PATH))
    quality_report = validator.run_checks(df)

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    processed_df = df.copy()
    if "date" in processed_df.columns:
        processed_df["date"] = processed_df["date"].dt.strftime("%Y-%m-%d")
    processed_df.to_csv(PROCESSED_PATH, index=False)

    with open(REPORT_PATH, "w") as f:
        json.dump(quality_report, f, indent=2, default=_json_default)

    monitor = KPIMonitor(str(MONITORING_CONFIG_PATH))
    monitoring_df = monitor.build_monitoring_table(processed_df)
    monitoring_df.to_csv(MONITORING_TABLE_PATH, index=False)
    monitoring_summary = monitor.write_monitoring_summary(
        monitoring_df,
        output_path=MONITORING_SUMMARY_PATH,
        monitoring_output_path=MONITORING_TABLE_PATH.relative_to(ROOT_DIR),
    )

    anomaly_detector = AnomalyDetector(config_path=str(MONITORING_CONFIG_PATH))
    anomaly_results = anomaly_detector.build_anomaly_results(monitoring_df, processed_df)
    anomaly_results.to_csv(ANOMALY_RESULTS_PATH, index=False)

    evaluator = ModelEvaluator()
    evaluation_df, comparison = evaluator.write_outputs(
        anomaly_results,
        evaluation_path=MODEL_EVALUATION_PATH,
        comparison_path=MODEL_COMPARISON_PATH,
        residual_model_used=anomaly_detector.residual_model_used,
        method_metadata={
            "residual_model_used": anomaly_detector.residual_model_used,
            "xgboost_used": anomaly_detector.residual_model_used == "xgboost_xgbregressor",
            "sklearn_used": anomaly_detector.residual_model_used == "sklearn_hist_gradient_boosting_regressor",
            "numpy_fallback_used": anomaly_detector.residual_model_used == "numpy_ridge_regression_residual",
            "train_split_date": anomaly_detector.residual_train_split_date,
            "feature_policy": (
                "Uses date, categorical dimensions, and prior moving_baseline. "
                "Excludes incident labels and current-day rolling averages."
            ),
            "fallback_note": (
                "XGBoost and scikit-learn are attempted first when importable; "
                "the deterministic NumPy ridge fallback is used when local native "
                "dependencies are unavailable."
            ),
        },
    )

    rca = RootCauseAnalyzer(config_path=str(MONITORING_CONFIG_PATH))
    rca_detector = rca.rca_config.get("default_detector", "residual_anomaly")
    rca_table = rca.build_contribution_table(anomaly_results, detector=rca_detector)
    RCA_TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    rca_table.to_csv(RCA_TABLE_PATH, index=False)
    total_rca_anomalies = rca.count_rca_candidates(anomaly_results, detector=rca_detector)
    rca_candidate_summary = rca.summarize_candidate_filter(anomaly_results, detector=rca_detector)
    rca_summary, top_root_causes = rca.write_outputs(
        rca_table,
        summary_path=ROOT_CAUSE_SUMMARY_PATH,
        top_causes_path=TOP_ROOT_CAUSES_PATH,
        detector=rca_detector,
        total_anomalies_analyzed=total_rca_anomalies,
        candidate_summary=rca_candidate_summary,
    )

    incident_reporter = IncidentReporter(config_path=str(MONITORING_CONFIG_PATH))
    incident_payload = incident_reporter.generate_reports(
        anomaly_results,
        rca_table,
        comparison,
        rca_summary,
        quality_report,
        monitoring_summary,
        json_path=LATEST_INCIDENT_JSON_PATH,
        markdown_path=LATEST_INCIDENT_MD_PATH,
        html_path=LATEST_INCIDENT_HTML_PATH,
        history_path=INCIDENT_HISTORY_PATH,
    )

    summary = {
        "raw_action": raw_action,
        "raw_rows": int(len(raw_df) if raw_df is not None else len(df)),
        "processed_rows": int(len(processed_df)),
        "health_score": int(quality_report["health_score"]),
        "status": quality_report["status"],
        "processed_path": str(PROCESSED_PATH.relative_to(ROOT_DIR)),
        "report_path": str(REPORT_PATH.relative_to(ROOT_DIR)),
        "monitoring_rows": int(len(monitoring_df)),
        "warning_count": int(monitoring_summary["warning_count"]),
        "critical_count": int(monitoring_summary["critical_count"]),
        "monitoring_table_path": str(MONITORING_TABLE_PATH.relative_to(ROOT_DIR)),
        "monitoring_summary_path": str(MONITORING_SUMMARY_PATH.relative_to(ROOT_DIR)),
        "anomaly_rows": int(len(anomaly_results)),
        "zscore_anomaly_count": int(anomaly_results["zscore_anomaly"].sum()),
        "residual_anomaly_count": int(anomaly_results["residual_anomaly"].sum()),
        "combined_anomaly_count": int(anomaly_results["combined_anomaly"].sum()),
        "anomaly_results_path": str(ANOMALY_RESULTS_PATH.relative_to(ROOT_DIR)),
        "model_evaluation_path": str(MODEL_EVALUATION_PATH.relative_to(ROOT_DIR)),
        "model_comparison_path": str(MODEL_COMPARISON_PATH.relative_to(ROOT_DIR)),
        "best_detector": comparison["best_detector"],
        "evaluation": evaluation_df.to_dict(orient="records"),
        "rca_detector": rca_detector,
        "rca_rows": int(len(rca_table)),
        "rca_anomalies_analyzed": int(total_rca_anomalies),
        "rca_table_path": str(RCA_TABLE_PATH.relative_to(ROOT_DIR)),
        "root_cause_summary_path": str(ROOT_CAUSE_SUMMARY_PATH.relative_to(ROOT_DIR)),
        "top_root_causes_path": str(TOP_ROOT_CAUSES_PATH.relative_to(ROOT_DIR)),
        "top_rca_statement": (
            rca_summary["top_root_cause_statements"][0]
            if rca_summary["top_root_cause_statements"]
            else "No RCA contributors found."
        ),
        "incidents_generated": int(incident_payload["incidents_generated"]),
        "highest_severity": incident_payload["highest_severity"],
        "highest_confidence_incident": incident_payload["highest_confidence_incident"],
        "latest_incident_json_path": str(LATEST_INCIDENT_JSON_PATH.relative_to(ROOT_DIR)),
        "latest_incident_md_path": str(LATEST_INCIDENT_MD_PATH.relative_to(ROOT_DIR)),
        "latest_incident_html_path": str(LATEST_INCIDENT_HTML_PATH.relative_to(ROOT_DIR)),
        "incident_history_path": str(INCIDENT_HISTORY_PATH.relative_to(ROOT_DIR)),
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 1 data foundation pipeline.")
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Regenerate deterministic raw KPI data before validation.",
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help=(
            "Anchor the generated dataset to this end date, e.g. $(date +%%F). "
            "Requires --regenerate. Omit to keep the pinned default end date that the "
            "published metrics were produced from. Use a current date to satisfy the "
            "14-day freshness check in the data quality layer."
        ),
    )
    args = parser.parse_args()

    if args.end_date and not args.regenerate:
        parser.error("--end-date has no effect without --regenerate")

    summary = run_phase_1_pipeline(regenerate=args.regenerate, end_date=args.end_date)

    print("KPI reliability pipeline complete")
    print(f"Raw rows {summary['raw_action']}: {summary['raw_rows']:,}")
    print(f"Validated rows written: {summary['processed_rows']:,}")
    print(f"Health score: {summary['health_score']}/100")
    print(f"Validation status: {summary['status']}")
    print(f"Monitoring rows written: {summary['monitoring_rows']:,}")
    print(f"WARNING rows: {summary['warning_count']:,}")
    print(f"CRITICAL rows: {summary['critical_count']:,}")
    print(f"Anomaly result rows written: {summary['anomaly_rows']:,}")
    print(f"Z-score anomalies: {summary['zscore_anomaly_count']:,}")
    print(f"Residual anomalies: {summary['residual_anomaly_count']:,}")
    print(f"Combined anomalies: {summary['combined_anomaly_count']:,}")
    print(f"Best detector by F1: {summary['best_detector']}")
    for row in summary["evaluation"]:
        print(
            f"  - {row['detector']}: "
            f"precision={row['precision']:.3f}, "
            f"recall={row['recall']:.3f}, "
            f"f1={row['f1_score']:.3f}"
        )
    print(f"RCA detector used: {summary['rca_detector']}")
    print(f"RCA anomalies analyzed: {summary['rca_anomalies_analyzed']:,}")
    print(f"RCA rows generated: {summary['rca_rows']:,}")
    print(f"Top RCA statement: {summary['top_rca_statement']}")
    print(f"Incidents generated: {summary['incidents_generated']:,}")
    print(f"Highest incident severity: {summary['highest_severity']}")
    print(f"Highest confidence incident: {summary['highest_confidence_incident']}")
    print(f"Processed data: {summary['processed_path']}")
    print(f"Data quality report: {summary['report_path']}")
    print(f"KPI monitoring table: {summary['monitoring_table_path']}")
    print(f"KPI monitoring summary: {summary['monitoring_summary_path']}")
    print(f"Anomaly results: {summary['anomaly_results_path']}")
    print(f"Model evaluation: {summary['model_evaluation_path']}")
    print(f"Model comparison: {summary['model_comparison_path']}")
    print(f"RCA contribution table: {summary['rca_table_path']}")
    print(f"Root cause summary: {summary['root_cause_summary_path']}")
    print(f"Top root causes: {summary['top_root_causes_path']}")
    print(f"Latest incident JSON: {summary['latest_incident_json_path']}")
    print(f"Latest incident Markdown: {summary['latest_incident_md_path']}")
    print(f"Latest incident HTML: {summary['latest_incident_html_path']}")
    print(f"Incident history: {summary['incident_history_path']}")


if __name__ == "__main__":
    main()
