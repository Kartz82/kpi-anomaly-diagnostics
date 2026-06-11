import json
import os
from datetime import datetime
import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

class ReportGenerator:
    """Generates human-readable console reports and machine-readable JSON artifacts."""
    
    def __init__(self, output_dir='data/reports', figures_dir='reports/figures'):
        self.output_dir = output_dir
        self.figures_dir = figures_dir
        self.logger = logging.getLogger(__name__)
        
        # Ensure output directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.figures_dir, exist_ok=True)

    def generate_report(self, health_results: dict, anomaly_results: dict, run_summary: dict | None = None):
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
        print(f"   - Status: {'PASS' if health_results['status'] == 'PASS' else 'FAIL'}")
        print(f"   - Health Score: {health_results['health_score']}/100")
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

        if run_summary:
            print(f"\n3. RUN SUMMARY")
            print(f"   - Observations Processed: {run_summary['total_observations_processed']}")
            print(f"   - Segment Combinations: {run_summary['total_segment_combinations_evaluated']}")
            print(f"   - KPI Families Configured: {run_summary['total_kpi_families_configured']}")
            print(f"   - Total Anomalies Detected: {run_summary['total_anomalies_detected']}")
            print(f"   - Diagnostic Runtime: {run_summary['diagnostic_runtime_seconds']}s")
        
        print("="*50)

        # 2. JSON Export (The Machine-Readable View)
        self._export_to_json(health_results, anomaly_results, run_summary)

    def generate_visualizations(
        self,
        df: pd.DataFrame,
        metric: str,
        anomaly_results: dict,
        run_summary: dict | None = None
    ):
        """Creates lightweight HTML charts for portfolio review and local inspection."""
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])

        artifact_paths = {
            "html": {
                "kpi_timeseries": os.path.join(self.output_dir, "kpi_timeseries.html"),
                "anomaly_zscore": os.path.join(self.output_dir, "anomaly_zscore.html"),
                "segment_root_cause": os.path.join(self.output_dir, "segment_root_cause.html")
            },
            "png": {
                "kpi_timeseries": os.path.join(self.figures_dir, "kpi_timeseries.png"),
                "anomaly_zscore": os.path.join(self.figures_dir, "anomaly_zscore.png"),
                "segment_root_cause": os.path.join(self.figures_dir, "segment_root_cause.png"),
                "incident_summary": os.path.join(self.figures_dir, "incident_summary.png")
            }
        }

        kpi_fig = self._build_kpi_timeseries(df, metric)
        zscore_fig = self._build_anomaly_zscore(df, metric)
        root_cause_fig = self._build_segment_root_cause(anomaly_results)
        incident_fig = self._build_incident_summary(metric, anomaly_results, run_summary)

        self._write_interactive_chart(kpi_fig, artifact_paths["html"]["kpi_timeseries"])
        self._write_interactive_chart(zscore_fig, artifact_paths["html"]["anomaly_zscore"])
        self._write_interactive_chart(root_cause_fig, artifact_paths["html"]["segment_root_cause"])

        self._write_static_chart(kpi_fig, artifact_paths["png"]["kpi_timeseries"])
        self._write_static_chart(zscore_fig, artifact_paths["png"]["anomaly_zscore"])
        self._write_static_chart(root_cause_fig, artifact_paths["png"]["segment_root_cause"])
        self._write_static_chart(incident_fig, artifact_paths["png"]["incident_summary"])

        print("Interactive HTML artifacts saved:")
        for path in artifact_paths["html"].values():
            print(f"   - {path}")
        print("Static PNG artifacts saved:")
        for path in artifact_paths["png"].values():
            print(f"   - {path}")

        return artifact_paths

    def generate_incident_center(self, incidents: list[dict]):
        """Creates a consolidated multi-KPI incident report."""
        html_path = os.path.join(self.output_dir, "incident_center.html")
        png_path = os.path.join(self.figures_dir, "incident_center.png")

        fig = self._build_incident_center(incidents)
        self._write_interactive_chart(fig, html_path)
        self._write_static_chart(fig, png_path)

        print("Incident Center artifacts saved:")
        print(f"   - {html_path}")
        print(f"   - {png_path}")

        return {"html": html_path, "png": png_path}

    def _build_kpi_timeseries(self, df: pd.DataFrame, metric: str):
        agg_func = "sum"
        if metric.endswith("_rate") or metric in {"ctr", "latency_ms"}:
            agg_func = "mean"

        daily_metric = df.groupby("date", as_index=False).agg({metric: agg_func})
        fig = px.line(
            daily_metric,
            x="date",
            y=metric,
            markers=True,
            title=f"{metric.replace('_', ' ').title()} Trend"
        )
        fig.update_layout(
            template="plotly_white",
            xaxis_title="Date",
            yaxis_title=metric,
            width=1100,
            height=650
        )
        return fig

    def _build_anomaly_zscore(self, df: pd.DataFrame, metric: str):
        zscore_col = f"{metric}_zscore"
        anomaly_col = f"{metric}_anomaly"
        daily_zscore = df.groupby("date", as_index=False).agg(
            max_abs_zscore=(zscore_col, lambda values: values.abs().max()),
            anomaly_count=(anomaly_col, "sum")
        )

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_zscore["date"],
            y=daily_zscore["max_abs_zscore"],
            mode="lines+markers",
            name="Max absolute Z-score"
        ))
        fig.add_hline(y=2.0, line_dash="dash", line_color="red", annotation_text="Alert threshold")
        fig.update_layout(
            title=f"{metric.replace('_', ' ').title()} Anomaly Z-Score",
            template="plotly_white",
            xaxis_title="Date",
            yaxis_title="Absolute Z-score",
            width=1100,
            height=650
        )
        return fig

    def _build_segment_root_cause(self, anomaly_results: dict):
        ranked_anomalies = anomaly_results.get("ranked_anomalies", [])
        if ranked_anomalies:
            chart_data = pd.DataFrame([
                {
                    "segment": " / ".join(item["segment"].values()),
                    "z_score": item["z_score"],
                    "actual_value": item["actual_value"],
                    "date": item["date"]
                }
                for item in ranked_anomalies
            ])
            fig = px.bar(
                chart_data,
                x="z_score",
                y="segment",
                orientation="h",
                color="z_score",
                hover_data=["date", "actual_value"],
                title="Top Segment-Level Root Causes"
            )
            fig.update_layout(
                template="plotly_white",
                yaxis_title="Segment",
                xaxis_title="Z-score",
                width=1100,
                height=700
            )
            fig.update_yaxes(autorange="reversed")
        else:
            fig = go.Figure()
            fig.add_annotation(
                text="No significant anomalies detected.",
                x=0.5,
                y=0.5,
                showarrow=False,
                font={"size": 18}
            )
            fig.update_layout(
                title="Segment-Level Root Cause",
                template="plotly_white",
                width=1100,
                height=650
            )

        return fig

    def _build_incident_summary(self, metric: str, anomaly_results: dict, run_summary: dict | None = None):
        fig = go.Figure()

        if anomaly_results.get("anomaly_detected"):
            offender = anomaly_results["primary_offender"]
            segment = " / ".join(offender["segment"].values())
            z_score = offender["z_score"]
            actual_value = offender["actual_value"]
            baseline = offender["rolling_mean"]
            incident_date = anomaly_results["date"]
            summary_text = f"<b>Primary segment:</b> {segment}<br><b>Date:</b> {incident_date}"
        else:
            z_score = 0
            actual_value = 0
            baseline = 0
            summary_text = "No significant anomaly detected."

        metrics_text = ""
        if run_summary:
            metrics_text = (
                f"<b>Observations processed:</b> {run_summary['total_observations_processed']} &nbsp; | &nbsp; "
                f"<b>Segment combinations:</b> {run_summary['total_segment_combinations_evaluated']} &nbsp; | &nbsp; "
                f"<b>KPI families:</b> {run_summary['total_kpi_families_configured']}<br>"
                f"<b>Anomalies detected:</b> {run_summary['total_anomalies_detected']} &nbsp; | &nbsp; "
                f"<b>Runtime:</b> {run_summary['diagnostic_runtime_seconds']}s"
            )

        fig.add_trace(go.Indicator(
            mode="number",
            value=z_score,
            title={"text": "Primary Z-score"},
            domain={"row": 0, "column": 0}
        ))
        fig.add_trace(go.Indicator(
            mode="number",
            value=actual_value,
            title={"text": "Actual KPI Value"},
            number={"valueformat": ".4f"},
            domain={"row": 0, "column": 1}
        ))
        fig.add_trace(go.Indicator(
            mode="number",
            value=baseline,
            title={"text": "Rolling Baseline"},
            number={"valueformat": ".4f"},
            domain={"row": 0, "column": 2}
        ))
        fig.add_annotation(
            text=summary_text,
            x=0.5,
            y=0.28,
            showarrow=False,
            font={"size": 20},
            align="center"
        )
        if metrics_text:
            fig.add_annotation(
                text=metrics_text,
                x=0.5,
                y=0.08,
                showarrow=False,
                font={"size": 17},
                align="center"
            )
        fig.update_layout(
            title=f"{metric.replace('_', ' ').title()} Incident Summary",
            template="plotly_white",
            grid={"rows": 1, "columns": 3},
            width=1100,
            height=620,
            margin={"t": 90, "b": 110}
        )
        return fig

    def _build_incident_center(self, incidents: list[dict]):
        if not incidents:
            incidents = [{
                "kpi": "No incidents",
                "current_value": "",
                "rolling_baseline": "",
                "z_score": "",
                "severity": "Normal",
                "primary_offender": "",
                "suggested_investigation": "No significant anomalies detected."
            }]

        severity_colors = {
            "Critical": "#fee2e2",
            "High": "#ffedd5",
            "Medium": "#fef9c3",
            "Normal": "#dcfce7"
        }
        severity_text_colors = {
            "Critical": "#991b1b",
            "High": "#9a3412",
            "Medium": "#854d0e",
            "Normal": "#166534"
        }

        headers = [
            "KPI",
            "Current Value",
            "Rolling Baseline",
            "Z-Score",
            "Severity",
            "Primary Offender",
            "Suggested Investigation"
        ]

        values = [
            [incident["kpi"] for incident in incidents],
            [incident["current_value"] for incident in incidents],
            [incident["rolling_baseline"] for incident in incidents],
            [incident["z_score"] for incident in incidents],
            [incident["severity"] for incident in incidents],
            [incident["primary_offender"] for incident in incidents],
            [incident["suggested_investigation"] for incident in incidents]
        ]
        severity_fill = [severity_colors.get(incident["severity"], "#f8fafc") for incident in incidents]
        severity_font = [severity_text_colors.get(incident["severity"], "#0f172a") for incident in incidents]

        fill_colors = [
            ["#f8fafc"] * len(incidents),
            ["#f8fafc"] * len(incidents),
            ["#f8fafc"] * len(incidents),
            ["#f8fafc"] * len(incidents),
            severity_fill,
            ["#f8fafc"] * len(incidents),
            ["#f8fafc"] * len(incidents)
        ]
        font_colors = [
            ["#0f172a"] * len(incidents),
            ["#0f172a"] * len(incidents),
            ["#0f172a"] * len(incidents),
            ["#0f172a"] * len(incidents),
            severity_font,
            ["#0f172a"] * len(incidents),
            ["#0f172a"] * len(incidents)
        ]

        fig = go.Figure(data=[go.Table(
            columnwidth=[1.1, 1, 1.15, 0.75, 0.8, 1.7, 3.2],
            header={
                "values": headers,
                "fill_color": "#1f2937",
                "font": {"color": "white", "size": 14},
                "align": "left",
                "height": 38
            },
            cells={
                "values": values,
                "fill_color": fill_colors,
                "font": {"color": font_colors, "size": 13},
                "align": "left",
                "height": 58
            }
        )])
        fig.update_layout(
            title="Incident Center: Multi-KPI Diagnostic Summary",
            template="plotly_white",
            width=1400,
            height=520,
            margin={"t": 80, "l": 24, "r": 24, "b": 24}
        )
        return fig

    def _write_interactive_chart(self, fig: go.Figure, file_path: str):
        fig.write_html(file_path, include_plotlyjs="cdn")

    def _write_static_chart(self, fig: go.Figure, file_path: str):
        fig.write_image(file_path, scale=2)

    def _export_to_json(self, health, anomalies, run_summary=None):
        """Saves a structured JSON file for integration with other tools."""
        report_data = {
            "metadata": {
                "report_generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "system_version": "1.0.0"
            },
            "run_summary": run_summary or {},
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
