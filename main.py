from src.core.ingestion import DataIngestor
from src.core.data_quality import DataQualityValidator
from src.core.anomaly_detection import AnomalyDetector
from src.core.root_cause import RootCauseAnalyzer
from src.core.reporting import ReportGenerator
import yaml

def main():
    # 0. Load Configuration
    config_path = "config/monitoring_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # 1. Ingest Data (Injecting a glitch to test our brain!)
    print("🚀 Step 1: Ingesting data...")
    ingestor = DataIngestor(config_path)
    df = ingestor.simulate_data(days=30, inject_glitch=True)

    # 2. Data Quality Gate
    print("🛡️  Step 2: Validating data quality...")
    validator = DataQualityValidator(config_path)
    dq_results = validator.run_checks(df)

    if not dq_results['is_healthy']:
        print(f"🛑 CRITICAL: Data quality check failed! Score: {dq_results['health_score']}")
        return

    # 3. Anomaly Detection (Monitoring Conversion Rate)
    print("🔍 Step 3: Running anomaly detection...")
    detector = AnomalyDetector(threshold=2.0)
    df_analyzed = detector.detect_anomalies(df, metric="conversions")

    # 4. Root Cause Analysis
    print("🧬 Step 4: Performing root cause analysis...")
    analyzer = RootCauseAnalyzer(segments=config['segments'])
    anomaly_summary = analyzer.analyze_failure(df_analyzed, metric="conversions")

    # 5. Reporting
    print("📝 Step 5: Generating final report...")
    reporter = ReportGenerator()
    reporter.generate_report(dq_results, anomaly_summary)

if __name__ == "__main__":
    main()