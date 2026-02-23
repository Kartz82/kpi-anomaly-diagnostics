import json
import os
from datetime import datetime
import logging

class ReportGenerator:
    """Generates human-readable console reports and machine-readable JSON artifacts."""
    
    def __init__(self, output_dir='data/reports'):
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        
        # Ensure the output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_report(self, health_results: dict, anomaly_results: dict):
        """
        Orchestrates the final output of the monitoring pipeline.
        
        Args:
            health_results: Output from DataQualityValidator
            anomaly_results: Output from RootCauseAnalyzer
        """
        
        # 1. Console Output (The Human-Readable View)
        print("\n" + "="*50)
        print("📊 KPI MONITORING DIAGNOSTIC REPORT")
        print("="*50)
        
        print(f"1. DATA QUALITY HEALTH")
        print(f"   - Status: {'✅ PASS' if health_results['status'] == 'PASS' else '❌ FAIL'}")
        print(f"   - Health Score: {health_results['score']}/100")
        print(f"   - Issues: {', '.join(health_results['issues']) if health_results['issues'] else 'None'}")
        
        print(f"\n2. ANOMALY DETECTION & ROOT CAUSE")
        if anomaly_results.get('anomaly_detected'):
            print(f"   - Metric Flagged: {anomaly_results['metric']}")
            print(f"   - Detection Date: {anomaly_results['date']}")
            print(f"   - Primary Offender: {{")
            print(f"        \"segment\": {json.dumps(anomaly_results['primary_offender']['segment'], indent=12)}")
            print(f"        \"z_score\": {anomaly_results['primary_offender']['z_score']:.2f},")
            print(f"        \"actual_value\": {anomaly_results['primary_offender']['actual_value']}")
            print(f"     }}")
        else:
            print("   - Status: No significant anomalies detected.")
        
        print("="*50)

        # 2. JSON Export (The Machine-Readable View)
        self._export_to_json(health_results, anomaly_results)

    def _export_to_json(self, health, anomalies):
        """Saves a structured JSON file for integration with other tools."""
        report_data = {
            "metadata": {
                "report_generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "system_version": "1.0.0"
            },
            "data_quality_summary": health,
            "diagnostic_details": anomalies
        }

        file_path = os.path.join(self.output_dir, "latest_diagnostic.json")
        
        try:
            with open(file_path, 'w') as f:
                json.dump(report_data, f, indent=4)
            print(f"📁 Structured report saved to: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to export JSON report: {e}")