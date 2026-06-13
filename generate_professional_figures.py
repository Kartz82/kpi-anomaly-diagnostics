from src.core.anomaly_detection import AnomalyDetector
from src.core.data_quality import DataQualityValidator
from src.core.ingestion import DataIngestor
from src.core.reporting import ReportGenerator
from src.core.root_cause import RootCauseAnalyzer
from main import build_incident_row
import json
import os
import time
import yaml

os.environ.setdefault(
    "BROWSER_PATH",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
)


def main():
    run_started_at = time.perf_counter()
    config_path = "config/monitoring_config.yaml"
    diagnostic_path = "data/reports/latest_diagnostic.json"

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    with open(diagnostic_path, "r") as f:
        saved_diagnostic = json.load(f)

    ingestor = DataIngestor(config_path)
    simulation_config = config.get("simulation", {})
    df = ingestor.simulate_data(
        days=simulation_config.get("days", 30),
        inject_glitch=simulation_config.get("inject_glitch", True),
        seed=simulation_config.get("seed", 42)
    )

    validator = DataQualityValidator(config_path)
    dq_results = validator.run_checks(df)
    if not dq_results["is_healthy"]:
        raise RuntimeError(f"Data quality check failed with score {dq_results['health_score']}")

    monitored_metric = config["kpis"][0]["name"]
    detector = AnomalyDetector(threshold=2.0, window=7)
    df_analyzed = detector.detect_anomalies(df, metric=monitored_metric)

    analyzer = RootCauseAnalyzer(segments=config["segments"])

    incident_rows = []
    for kpi_config in config["kpis"]:
        metric = kpi_config["name"]
        metric_analyzed = detector.detect_anomalies(df, metric=metric)
        metric_summary = analyzer.analyze_failure(metric_analyzed, metric=metric)
        incident_rows.append(build_incident_row(metric, metric_summary))

    anomaly_summary = saved_diagnostic["diagnostic_details"]
    run_summary = saved_diagnostic["run_summary"]

    reporter = ReportGenerator()
    reporter.generate_professional_portfolio_figures(
        metric=monitored_metric,
        anomaly_results=anomaly_summary,
        run_summary=run_summary,
        incidents=incident_rows
    )


if __name__ == "__main__":
    main()
