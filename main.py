from src.core.ingestion import DataIngestor
from src.core.data_quality import DataQualityValidator
from src.core.anomaly_detection import AnomalyDetector
from src.core.root_cause import RootCauseAnalyzer
from src.core.reporting import ReportGenerator
import time
import yaml

def get_severity(z_score: float) -> str:
    abs_z = abs(z_score)
    if abs_z >= 5:
        return "Critical"
    if abs_z >= 3:
        return "High"
    if abs_z >= 2:
        return "Medium"
    return "Normal"

def get_suggested_investigation(metric: str, segment: dict) -> str:
    segment_key = (
        segment.get("device_type"),
        segment.get("region"),
        segment.get("browser")
    )
    suggestions = {
        ("conversion_rate", ("Mobile", "EMEA", "Safari")): (
            "Check mobile Safari checkout flow, consent/tracking changes, or regional deployment issue."
        ),
        ("ctr", ("Desktop", "NA", "Chrome")): (
            "Check campaign creative, homepage module changes, or tracking implementation."
        ),
        ("latency_ms", ("Mobile", "APAC", "Firefox")): (
            "Check regional latency, CDN routing, or frontend performance regression."
        )
    }
    return suggestions.get(
        (metric, segment_key),
        "Review the affected segment for recent product, tracking, campaign, or performance changes."
    )

def build_incident_row(metric: str, anomaly_summary: dict) -> dict:
    if not anomaly_summary.get("anomaly_detected"):
        return {
            "kpi": metric,
            "current_value": "N/A",
            "rolling_baseline": "N/A",
            "z_score": "0.00",
            "severity": "Normal",
            "primary_offender": "No anomaly detected",
            "suggested_investigation": "No immediate investigation suggested."
        }

    offender = anomaly_summary["primary_offender"]
    segment = offender["segment"]
    z_score = float(offender["z_score"])

    return {
        "kpi": metric,
        "current_value": f"{offender['actual_value']:.4f}",
        "rolling_baseline": f"{offender['rolling_mean']:.4f}",
        "z_score": f"{z_score:.2f}",
        "severity": get_severity(z_score),
        "primary_offender": " / ".join(segment.values()),
        "suggested_investigation": get_suggested_investigation(metric, segment)
    }

def main():
    run_started_at = time.perf_counter()

    # 0. Load Configuration
    config_path = "config/monitoring_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # 1. Ingest Data
    print("🚀 Step 1: Ingesting data...")
    ingestor = DataIngestor(config_path)
    simulation_config = config.get("simulation", {})
    df = ingestor.simulate_data(
        days=simulation_config.get("days", 30),
        inject_glitch=simulation_config.get("inject_glitch", True),
        seed=simulation_config.get("seed", 42)
    )

    # 2. Data Quality Gate
    print("🛡️  Step 2: Validating data quality...")
    validator = DataQualityValidator(config_path)
    dq_results = validator.run_checks(df)

    if not dq_results['is_healthy']:
        print(f"🛑 CRITICAL: Data quality check failed! Score: {dq_results['health_score']}")
        return

    # 3. Anomaly Detection (Monitoring Conversion Rate)
    print("🔍 Step 3: Running anomaly detection...")
    monitored_metric = config["kpis"][0]["name"]
    detector = AnomalyDetector(threshold=2.0, window=7)
    df_analyzed = detector.detect_anomalies(df, metric=monitored_metric)

    # 4. Root Cause Analysis
    print("🧬 Step 4: Performing root cause analysis...")
    analyzer = RootCauseAnalyzer(segments=config['segments'])
    anomaly_summary = analyzer.analyze_failure(df_analyzed, metric=monitored_metric)

    incident_rows = []
    for kpi_config in config["kpis"]:
        metric = kpi_config["name"]
        metric_analyzed = detector.detect_anomalies(df, metric=metric)
        metric_summary = analyzer.analyze_failure(metric_analyzed, metric=metric)
        incident_rows.append(build_incident_row(metric, metric_summary))

    anomaly_col = f"{monitored_metric}_anomaly"
    zscore_col = f"{monitored_metric}_zscore"
    run_summary = {
        "total_observations_processed": int(len(df_analyzed)),
        "total_kpi_families_configured": int(len(config["kpis"])),
        "monitored_kpi": monitored_metric,
        "total_segment_combinations_evaluated": int(df_analyzed[config["segments"]].drop_duplicates().shape[0]),
        "rolling_baseline_window": int(detector.window),
        "total_anomalies_detected": int(df_analyzed[anomaly_col].sum()),
        "max_abs_z_score": round(float(df_analyzed[zscore_col].abs().max()), 2),
        "diagnostic_runtime_seconds": round(time.perf_counter() - run_started_at, 2)
    }

    # 5. Reporting
    print("📝 Step 5: Generating final report...")
    reporter = ReportGenerator()
    reporter.generate_report(dq_results, anomaly_summary, run_summary)

    print("📈 Step 6: Generating visual artifacts...")
    reporter.generate_visualizations(
        df_analyzed,
        metric=monitored_metric,
        anomaly_results=anomaly_summary,
        run_summary=run_summary
    )

    print("🧭 Step 7: Generating Incident Center...")
    reporter.generate_incident_center(incident_rows)

if __name__ == "__main__":
    main()
