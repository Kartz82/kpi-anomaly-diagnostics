import json
import os

class ReportGenerator:
    def __init__(self, output_dir: str = "data/reports"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_summary(self, dq_report: dict, anomaly_summary: dict):
        """Prints and saves a structured diagnostic report."""
        
        report_text = f"""
{'='*40}
📊 KPI MONITORING DIAGNOSTIC REPORT
{'='*40}
1. DATA QUALITY HEALTH
   - Status: {'✅ PASS' if dq_report['is_healthy'] else '❌ FAIL'}
   - Health Score: {dq_report['health_score']}/100
   - Issues: {', '.join(dq_report['failed_checks']) if dq_report['failed_checks'] else 'None'}

2. ANOMALY DETECTION & ROOT CAUSE
   - Metric Flagged: {anomaly_summary.get('metric', 'N/A')}
   - Detection Date: {anomaly_summary.get('detected_on', 'N/A')}
   - Primary Offender: {json.dumps(anomaly_summary.get('primary_offender', {}), indent=7)}
{'='*40}
"""
        print(report_text)
        
        # Save to disk for record keeping
        with open(f"{self.output_dir}/latest_diagnostic.txt", "w") as f:
            f.write(report_text)