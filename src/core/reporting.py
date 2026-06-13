import json
import os
import textwrap
from datetime import datetime
import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

BACKGROUND = "#050A14"
PANEL = "#0B1220"
CARD = "#111827"
BORDER = "#243244"
GRID = "rgba(148, 163, 184, 0.16)"
TEXT = "#E5E7EB"
MUTED = "#94A3B8"

BLUE = "#38BDF8"
TEAL = "#14B8A6"
GREEN = "#10B981"
AMBER = "#F59E0B"
ORANGE = "#F97316"
ROSE = "#FB7185"
RED = "#F43F5E"
PURPLE = "#A855F7"
GRAY = "#64748B"

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

    def generate_professional_portfolio_figures(
        self,
        metric: str,
        anomaly_results: dict,
        run_summary: dict,
        incidents: list[dict]
    ):
        """Creates dark-theme portfolio PNGs without modifying the standard report outputs."""
        artifact_paths = {
            "incident_center": os.path.join(self.figures_dir, "incident_center_professional.png"),
            "kpi_summary": os.path.join(self.figures_dir, "kpi_summary_professional.png"),
            "root_cause_analysis": os.path.join(self.figures_dir, "root_cause_analysis_professional.png")
        }

        figures = {
            "incident_center": self._build_professional_incident_center(incidents),
            "kpi_summary": self._build_professional_kpi_summary(metric, anomaly_results, run_summary),
            "root_cause_analysis": self._build_professional_root_cause(anomaly_results)
        }

        for name, fig in figures.items():
            self._write_professional_chart(fig, artifact_paths[name])

        print("Professional portfolio PNG artifacts saved:")
        for path in artifact_paths.values():
            print(f"   - {path}")

        return artifact_paths

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

    def _build_professional_incident_center(self, incidents: list[dict]):
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

        headers = [
            "KPI",
            "Current",
            "Baseline",
            "Z-score",
            "Severity",
            "Primary Offender",
            "Suggested Investigation"
        ]
        values = [
            [incident["kpi"] for incident in incidents],
            [incident["current_value"] for incident in incidents],
            [incident["rolling_baseline"] for incident in incidents],
            [incident["z_score"] for incident in incidents],
            [f"<b>{incident['severity']}</b>" for incident in incidents],
            [incident["primary_offender"] for incident in incidents],
            [self._wrap_html(incident["suggested_investigation"], 54) for incident in incidents]
        ]

        severity_fill = []
        severity_font = []
        for incident in incidents:
            severity = incident["severity"]
            if severity == "Critical":
                severity_fill.append("rgba(244, 63, 94, 0.22)")
                severity_font.append(ROSE)
            elif severity == "High":
                severity_fill.append("rgba(249, 115, 22, 0.18)")
                severity_font.append(ORANGE)
            elif severity == "Medium":
                severity_fill.append("rgba(245, 158, 11, 0.16)")
                severity_font.append(AMBER)
            else:
                severity_fill.append("rgba(16, 185, 129, 0.14)")
                severity_font.append(GREEN)

        row_count = len(incidents)
        fill_colors = [
            [PANEL] * row_count,
            [PANEL] * row_count,
            [PANEL] * row_count,
            [PANEL] * row_count,
            severity_fill,
            [PANEL] * row_count,
            [PANEL] * row_count
        ]
        font_colors = [
            [TEXT] * row_count,
            [TEXT] * row_count,
            [TEXT] * row_count,
            [TEXT] * row_count,
            severity_font,
            [TEXT] * row_count,
            [TEXT] * row_count
        ]

        fig = go.Figure(data=[go.Table(
            domain={"x": [0.035, 0.965], "y": [0.10, 0.82]},
            columnwidth=[1.0, 0.86, 0.94, 0.72, 0.82, 1.65, 3.45],
            header={
                "values": [f"<b>{header}</b>" for header in headers],
                "fill_color": CARD,
                "line": {"color": BORDER, "width": 1},
                "font": {"color": TEXT, "size": 21},
                "align": "left",
                "height": 62
            },
            cells={
                "values": values,
                "fill_color": fill_colors,
                "line": {"color": BORDER, "width": 1},
                "font": {"color": font_colors, "size": 19},
                "align": "left",
                "height": 148
            }
        )])
        fig.update_layout(
            title={
                "text": "Incident Center: Multi-KPI Diagnostic Summary",
                "x": 0.035,
                "y": 0.955,
                "font": {"size": 32, "color": TEXT}
            },
            paper_bgcolor=BACKGROUND,
            plot_bgcolor=BACKGROUND,
            width=1600,
            height=900,
            margin={"t": 105, "l": 42, "r": 42, "b": 55},
            font={"family": "Arial", "color": TEXT}
        )
        return fig

    def _build_professional_kpi_summary(
        self,
        metric: str,
        anomaly_results: dict,
        run_summary: dict
    ):
        offender = anomaly_results.get("primary_offender", {})
        segment = " / ".join(offender.get("segment", {}).values()) or "No anomaly detected"
        z_score = float(offender.get("z_score", 0))
        actual_value = float(offender.get("actual_value", 0))
        baseline = float(offender.get("rolling_mean", 0))
        incident_date = anomaly_results.get("date", "N/A")

        fig = go.Figure()
        fig.update_layout(
            title={
                "text": f"{metric.replace('_', ' ').title()} Incident Summary",
                "x": 0.055,
                "y": 0.955,
                "font": {"size": 34, "color": TEXT}
            },
            width=1600,
            height=900,
            paper_bgcolor=BACKGROUND,
            plot_bgcolor=BACKGROUND,
            margin={"t": 100, "l": 50, "r": 50, "b": 55},
            xaxis={"visible": False, "range": [0, 100]},
            yaxis={"visible": False, "range": [0, 100]},
            font={"family": "Arial", "color": TEXT}
        )

        fig.add_annotation(
            text="Control tower summary for the primary conversion-rate anomaly",
            x=0.055,
            y=0.875,
            xref="paper",
            yref="paper",
            showarrow=False,
            align="left",
            xanchor="left",
            font={"size": 18, "color": MUTED}
        )

        cards = [
            (0.055, 0.46, 0.31, 0.73, "Primary Z-score", f"{z_score:.2f}", ROSE),
            (0.3725, 0.46, 0.6275, 0.73, "Actual KPI Value", f"{actual_value:.4f}", BLUE),
            (0.69, 0.46, 0.945, 0.73, "Rolling Baseline", f"{baseline:.4f}", TEAL)
        ]
        for x0, y0, x1, y1, label, value, color in cards:
            self._add_paper_card(fig, x0, y0, x1, y1, color)
            fig.add_annotation(x=x0 + 0.02, y=y1 - 0.06, text=label, showarrow=False,
                               xref="paper", yref="paper", align="left", xanchor="left",
                               font={"size": 20, "color": MUTED})
            fig.add_annotation(x=(x0 + x1) / 2, y=y0 + 0.11, text=f"<b>{value}</b>",
                               xref="paper", yref="paper", showarrow=False,
                               font={"size": 54, "color": color})

        self._add_paper_card(fig, 0.055, 0.27, 0.945, 0.405, BLUE, opacity=0.12)
        fig.add_annotation(
            x=0.08,
            y=0.36,
            xref="paper",
            yref="paper",
            text=f"<b>Primary segment:</b> {segment}",
            showarrow=False,
            align="left",
            xanchor="left",
            font={"size": 24, "color": TEXT}
        )
        fig.add_annotation(
            x=0.08,
            y=0.305,
            xref="paper",
            yref="paper",
            text=f"<b>Date:</b> {incident_date}",
            showarrow=False,
            align="left",
            xanchor="left",
            font={"size": 22, "color": MUTED}
        )

        metric_cards = [
            ("Observations processed", f"{run_summary['total_observations_processed']:,}", BLUE),
            ("Segment combinations", f"{run_summary['total_segment_combinations_evaluated']}", TEAL),
            ("KPI families", f"{run_summary['total_kpi_families_configured']}", PURPLE),
            ("Anomalies detected", f"{run_summary['total_anomalies_detected']}", ROSE),
            ("Runtime", f"{run_summary['diagnostic_runtime_seconds']}s", GREEN)
        ]
        start_x = 0.055
        width = 0.166
        gap = 0.014
        for index, (label, value, color) in enumerate(metric_cards):
            x0 = start_x + index * (width + gap)
            self._add_paper_card(fig, x0, 0.08, x0 + width, 0.205, color, opacity=0.1)
            fig.add_annotation(x=x0 + 0.012, y=0.165, text=label, showarrow=False,
                               xref="paper", yref="paper", align="left", xanchor="left",
                               font={"size": 14, "color": MUTED})
            fig.add_annotation(x=x0 + 0.012, y=0.112, text=f"<b>{value}</b>", showarrow=False,
                               xref="paper", yref="paper", align="left", xanchor="left",
                               font={"size": 28, "color": color})

        return fig

    def _build_professional_root_cause(self, anomaly_results: dict):
        ranked_anomalies = anomaly_results.get("ranked_anomalies", [])
        if not ranked_anomalies:
            fig = go.Figure()
            fig.add_annotation(text="No significant anomalies detected.", x=0.5, y=0.5,
                               showarrow=False, font={"size": 24, "color": TEXT})
            fig.update_layout(width=1600, height=900, paper_bgcolor=BACKGROUND, plot_bgcolor=BACKGROUND)
            return fig

        chart_data = pd.DataFrame([
            {
                "segment": " · ".join(item["segment"].values()),
                "z_score": float(item["z_score"]),
                "actual_value": item["actual_value"],
                "date": item["date"]
            }
            for item in ranked_anomalies
        ])
        chart_data = chart_data.sort_values(
            by="z_score",
            key=lambda values: values.abs(),
            ascending=False
        )
        primary_segment = " / ".join(
            anomaly_results.get("primary_offender", {}).get("segment", {}).values()
        )
        primary_label = " · ".join(
            anomaly_results.get("primary_offender", {}).get("segment", {}).values()
        )

        colors = []
        line_colors = []
        line_widths = []
        for _, row in chart_data.iterrows():
            if row["segment"] == primary_label:
                colors.append(RED)
                line_colors.append("#FDA4AF")
                line_widths.append(2.1)
            elif row["z_score"] < 0:
                colors.append(ROSE)
                line_colors.append("rgba(229, 231, 235, 0.18)")
                line_widths.append(0.7)
            else:
                colors.append(ORANGE if row["z_score"] >= 4 else AMBER)
                line_colors.append("rgba(229, 231, 235, 0.18)")
                line_widths.append(0.7)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=chart_data["z_score"],
            y=chart_data["segment"],
            orientation="h",
            marker={
                "color": colors,
                "line": {"color": line_colors, "width": line_widths}
            },
            width=0.52,
            hovertemplate="<b>%{y}</b><br>Z-score: %{x:.2f}<extra></extra>",
            cliponaxis=False
        ))
        fig.add_vline(x=0, line_width=2, line_color="rgba(229, 231, 235, 0.66)")

        primary_row = chart_data[chart_data["segment"] == primary_label]
        for _, row in chart_data.iterrows():
            z_score = float(row["z_score"])
            if z_score < 0:
                label_x = z_score - 0.24
                xanchor = "right"
            else:
                label_x = z_score + 0.24
                xanchor = "left"
            fig.add_annotation(
                x=label_x,
                y=row["segment"],
                text=f"{z_score:+.2f}",
                showarrow=False,
                xanchor=xanchor,
                align="center",
                font={"size": 17, "color": TEXT}
            )

        primary_callout = ""
        if not primary_row.empty:
            primary_z_score = float(primary_row.iloc[0]["z_score"])
            primary_callout = f"<b>Primary offender:</b> {primary_label} | Z-score: {primary_z_score:.2f}"

        fig.update_layout(
            title={
                "text": "Top Segment-Level Root Causes",
                "x": 0.045,
                "y": 0.955,
                "font": {"size": 36, "color": TEXT}
            },
            width=1600,
            height=900,
            paper_bgcolor=BACKGROUND,
            plot_bgcolor=PANEL,
            margin={"l": 440, "r": 120, "t": 170, "b": 140},
            font={"family": "Arial", "color": TEXT},
            xaxis={
                "title": {"text": "Z-score deviation", "font": {"size": 20, "color": MUTED}},
                "range": [-11, 6],
                "gridcolor": GRID,
                "zeroline": False,
                "showline": False,
                "tickfont": {"size": 17, "color": MUTED}
            },
            yaxis={
                "title": "",
                "autorange": "reversed",
                "automargin": True,
                "tickfont": {"size": 18, "color": TEXT}
            },
            bargap=0.33,
            showlegend=False
        )
        fig.add_annotation(
            text="Largest KPI deviations by device, region, and browser",
            x=0.045,
            y=1.09,
            xref="paper",
            yref="paper",
            showarrow=False,
            align="left",
            xanchor="left",
            font={"size": 19, "color": MUTED}
        )
        if primary_callout:
            fig.add_annotation(
                text=primary_callout,
                x=0.955,
                y=1.09,
                xref="paper",
                yref="paper",
                showarrow=False,
                xanchor="right",
                font={"size": 18, "color": TEXT},
                bgcolor="rgba(17, 24, 39, 0.94)",
                bordercolor=BORDER,
                borderpad=8
            )
        fig.add_annotation(
            text="Negative values indicate KPI underperformance",
            x=0.0,
            y=-0.14,
            xref="paper",
            yref="paper",
            showarrow=False,
            xanchor="left",
            font={"size": 16, "color": MUTED}
        )
        fig.add_shape(
            type="rect",
            x0=0,
            y0=0,
            x1=1,
            y1=1,
            xref="paper",
            yref="paper",
            line={"color": BORDER, "width": 1},
            fillcolor="rgba(0, 0, 0, 0)",
            layer="below"
        )
        return fig

    def _add_paper_card(self, fig: go.Figure, x0, y0, x1, y1, accent, opacity=0.16):
        fig.add_shape(
            type="rect",
            x0=x0,
            y0=y0,
            x1=x1,
            y1=y1,
            xref="paper",
            yref="paper",
            line={"color": BORDER, "width": 1.2},
            fillcolor=CARD,
            layer="below"
        )
        fig.add_shape(
            type="rect",
            x0=x0,
            y0=y1 - 0.014,
            x1=x1,
            y1=y1,
            xref="paper",
            yref="paper",
            line={"color": accent, "width": 0},
            fillcolor=accent,
            opacity=opacity,
            layer="below"
        )

    def _add_card(self, fig: go.Figure, x0, y0, x1, y1, accent, opacity=0.16):
        fig.add_shape(
            type="rect",
            x0=x0,
            y0=y0,
            x1=x1,
            y1=y1,
            line={"color": BORDER, "width": 1.2},
            fillcolor=CARD,
            layer="below"
        )
        fig.add_shape(
            type="rect",
            x0=x0,
            y0=y1 - 1.4,
            x1=x1,
            y1=y1,
            line={"color": accent, "width": 0},
            fillcolor=accent,
            opacity=opacity,
            layer="below"
        )

    def _wrap_html(self, value: str, width: int):
        return "<br>".join(textwrap.wrap(value, width=width, break_long_words=False))

    def _write_interactive_chart(self, fig: go.Figure, file_path: str):
        fig.write_html(file_path, include_plotlyjs="cdn")

    def _write_static_chart(self, fig: go.Figure, file_path: str):
        fig.write_image(file_path, scale=2)

    def _write_professional_chart(self, fig: go.Figure, file_path: str):
        fig.write_image(file_path, width=1600, height=900, scale=2)

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
