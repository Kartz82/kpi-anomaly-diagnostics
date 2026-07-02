from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml


SEVERITY_RANK = {"NORMAL": 0, "INFO": 0, "WARNING": 1, "CRITICAL": 2}


class IncidentReporter:
    def __init__(self, config_path: str = "config/monitoring_config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        self.incident_config = self.config.get("incident_reporting", {})
        self.kpi_directions = {
            kpi: values.get("direction", "lower_is_bad")
            for kpi, values in self.config.get("kpi_monitoring", {}).get("thresholds", {}).items()
        }

    def build_incidents(
        self,
        anomaly_results: pd.DataFrame,
        rca_table: pd.DataFrame,
        model_comparison: dict,
        root_cause_summary: dict,
        data_quality_report: dict,
        monitoring_summary: dict,
    ) -> list[dict]:
        detector = self.incident_config.get("default_detector", "residual_anomaly")
        severity_column = self._severity_column(detector)
        max_incidents = int(self.incident_config.get("max_incidents", 12))
        max_root_causes = int(self.incident_config.get("max_root_causes_per_incident", 3))
        max_actions = int(self.incident_config.get("max_actions_per_incident", 3))

        candidates = anomaly_results[
            (anomaly_results[detector].astype(bool))
            & (anomaly_results[severity_column].isin(["WARNING", "CRITICAL"]))
            & (anomaly_results["expected_value"].notna())
            & (anomaly_results["percent_variance"].notna())
        ].copy()
        if candidates.empty:
            return []

        incidents = []
        for (incident_date, kpi_name), group in candidates.groupby(["date", "kpi_name"]):
            rca_group = rca_table[
                (rca_table["analysis_date"].astype(str) == str(incident_date))
                & (rca_table["kpi_name"] == kpi_name)
                & (rca_table["detector_used"] == detector)
            ].copy()
            top_root_causes = self._top_root_causes(rca_group, max_root_causes)
            severity = self._incident_severity(kpi_name, group, top_root_causes, severity_column)
            confidence_score = self._confidence_score(
                group,
                top_root_causes,
                model_comparison,
                data_quality_report,
                severity_column,
            )
            confidence_label = self._confidence_label(confidence_score)
            actions = self._recommended_actions(kpi_name, top_root_causes, max_actions)
            top_cause_text = (
                top_root_causes[0]["dimension_value"]
                if top_root_causes
                else "the affected segment"
            )
            executive_summary = self._executive_summary(
                incident_date,
                kpi_name,
                severity,
                detector,
                top_root_causes,
                actions,
            )

            incident = {
                "incident_id": self._incident_id(incident_date, kpi_name, detector),
                "incident_date": str(incident_date),
                "kpi_affected": kpi_name,
                "severity": severity,
                "confidence_score": confidence_score,
                "confidence_label": confidence_label,
                "detector_used": detector,
                "actual_value_summary": round(float(group["actual_value"].mean()), 6),
                "expected_value_summary": round(float(group["expected_value"].mean()), 6),
                "percent_variance_summary": round(float(group["percent_variance"].mean()), 6),
                "anomaly_count": int(len(group)),
                "suspected_dimensions": [cause["dimension_value"] for cause in top_root_causes],
                "top_root_causes": top_root_causes,
                "recommended_actions": actions,
                "executive_summary": executive_summary,
                "supporting_metrics": {
                    "max_abs_percent_variance": round(float(group["percent_variance"].abs().max()), 6),
                    "max_detector_severity": self._max_severity(group[severity_column]),
                    "top_root_cause": top_cause_text,
                    "monitoring_warning_count": int(monitoring_summary.get("warning_count", 0)),
                    "monitoring_critical_count": int(monitoring_summary.get("critical_count", 0)),
                },
                "data_quality_context": {
                    "status": data_quality_report.get("status"),
                    "health_score": data_quality_report.get("health_score"),
                },
                "model_context": {
                    "best_detector": model_comparison.get("best_detector"),
                    "best_detector_f1_score": model_comparison.get("best_detector_f1_score"),
                    "residual_model_used": model_comparison.get("residual_model_used"),
                    "method_metadata": model_comparison.get("method_metadata", {}),
                },
            }
            incidents.append(incident)

        incidents = sorted(
            incidents,
            key=lambda item: (
                SEVERITY_RANK.get(item["severity"], 0),
                item["confidence_score"],
                item["anomaly_count"],
            ),
            reverse=True,
        )
        return self._diversify_incidents(incidents, max_incidents)

    def write_outputs(
        self,
        incidents: list[dict],
        json_path: str | Path = "data/reports/latest_incident.json",
        markdown_path: str | Path = "data/reports/latest_incident.md",
        html_path: str | Path = "data/reports/latest_incident.html",
        history_path: str | Path = "data/reports/incident_history.csv",
    ) -> dict:
        json_path = Path(json_path)
        markdown_path = Path(markdown_path)
        html_path = Path(html_path)
        history_path = Path(history_path)
        for path in [json_path, markdown_path, html_path, history_path]:
            path.parent.mkdir(parents=True, exist_ok=True)

        highest = incidents[0] if incidents else None
        payload = {
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "detector_used": self.incident_config.get("default_detector", "residual_anomaly"),
            "incidents_generated": len(incidents),
            "highest_severity": highest["severity"] if highest else "NORMAL",
            "highest_confidence_incident": highest["incident_id"] if highest else None,
            "incidents": incidents,
            "confidence_method_notes": (
                "Practical triage score, not a statistical probability. It combines "
                "detector F1, RCA concentration, data quality score, anomaly support, "
                "and detector severity using configured weights."
            ),
            "limitations": [
                "Incident reports are generated from deterministic synthetic data.",
                "Recommended actions are rule based and should guide investigation, not prove causality.",
            ],
        }

        with open(json_path, "w") as f:
            json.dump(payload, f, indent=2)

        markdown = self._render_markdown(payload)
        markdown_path.write_text(markdown)
        html_path.write_text(self._render_html(markdown, payload))
        self._write_history(incidents, history_path)
        return payload

    def generate_reports(
        self,
        anomaly_results: pd.DataFrame,
        rca_table: pd.DataFrame,
        model_comparison: dict,
        root_cause_summary: dict,
        data_quality_report: dict,
        monitoring_summary: dict,
        json_path: str | Path = "data/reports/latest_incident.json",
        markdown_path: str | Path = "data/reports/latest_incident.md",
        html_path: str | Path = "data/reports/latest_incident.html",
        history_path: str | Path = "data/reports/incident_history.csv",
    ) -> dict:
        incidents = self.build_incidents(
            anomaly_results,
            rca_table,
            model_comparison,
            root_cause_summary,
            data_quality_report,
            monitoring_summary,
        )
        return self.write_outputs(incidents, json_path, markdown_path, html_path, history_path)

    def _top_root_causes(self, rca_group: pd.DataFrame, max_root_causes: int) -> list[dict]:
        if rca_group.empty:
            return []
        preferred = rca_group[rca_group["dimension_type"].isin(["region_device_browser", "full_segment"])]
        if preferred.empty:
            preferred = rca_group
        top = (
            preferred.sort_values(["contribution_share", "degradation_amount"], ascending=False)
            .drop_duplicates(subset=["dimension_type", "dimension_value"])
            .head(max_root_causes)
        )
        return [
            {
                "dimension_type": row["dimension_type"],
                "dimension_value": row["dimension_value"],
                "contribution_share": round(float(row["contribution_share"]), 6),
                "degradation_amount": round(float(row["degradation_amount"]), 6),
                "severity": row["severity_max"],
                "recommended_action": row["recommended_action"],
            }
            for _, row in top.iterrows()
        ]

    def _incident_severity(
        self,
        kpi_name: str,
        group: pd.DataFrame,
        top_root_causes: list[dict],
        severity_column: str,
    ) -> str:
        max_detector = self._max_severity(group[severity_column])
        max_abs_pct = float(group["percent_variance"].abs().max())
        concentration = max((cause["contribution_share"] for cause in top_root_causes), default=0)
        severity_thresholds = self.incident_config.get("severity_thresholds", {})
        critical_pct = float(severity_thresholds.get("critical_percent_variance", 0.30))
        warning_pct = float(severity_thresholds.get("warning_percent_variance", 0.15))
        critical_concentration = float(severity_thresholds.get("critical_contribution_share", 0.60))

        if (
            max_detector == "CRITICAL"
            or max_abs_pct >= critical_pct
            or concentration >= critical_concentration and max_abs_pct >= warning_pct
        ):
            return "CRITICAL"
        if max_detector == "WARNING" or max_abs_pct >= warning_pct:
            return "WARNING"
        return "NORMAL"

    def _confidence_score(
        self,
        group: pd.DataFrame,
        top_root_causes: list[dict],
        model_comparison: dict,
        data_quality_report: dict,
        severity_column: str,
    ) -> float:
        weights = self.incident_config.get("confidence_weights", {})
        model_f1 = float(model_comparison.get("best_detector_f1_score", 0))
        top_share = max((cause["contribution_share"] for cause in top_root_causes), default=0)
        dq_score = float(data_quality_report.get("health_score", 0)) / 100
        anomaly_support = min(len(group) / float(self.incident_config.get("support_saturation_count", 10)), 1.0)
        severity_score = 1.0 if self._max_severity(group[severity_column]) == "CRITICAL" else 0.65

        score = (
            float(weights.get("model_f1", 0.30)) * model_f1
            + float(weights.get("rca_concentration", 0.30)) * top_share
            + float(weights.get("data_quality", 0.20)) * dq_score
            + float(weights.get("anomaly_support", 0.10)) * anomaly_support
            + float(weights.get("severity", 0.10)) * severity_score
        )
        return round(max(0.0, min(1.0, score)), 3)

    @staticmethod
    def _confidence_label(score: float) -> str:
        if score >= 0.80:
            return "High"
        if score >= 0.55:
            return "Medium"
        return "Low"

    @staticmethod
    def _diversify_incidents(incidents: list[dict], max_incidents: int) -> list[dict]:
        if not incidents:
            return []
        selected = []
        seen_ids = set()
        for _, group in pd.DataFrame(incidents).groupby("kpi_affected", sort=False):
            best = group.iloc[0].to_dict()
            selected.append(best)
            seen_ids.add(best["incident_id"])

        for incident in incidents:
            if len(selected) >= max_incidents:
                break
            if incident["incident_id"] not in seen_ids:
                selected.append(incident)
                seen_ids.add(incident["incident_id"])

        return selected[:max_incidents]

    def _recommended_actions(self, kpi_name: str, top_root_causes: list[dict], max_actions: int) -> list[str]:
        cause_text = " ".join(cause["dimension_value"] for cause in top_root_causes)
        actions = []
        if kpi_name == "conversion_rate":
            if "Mobile" in cause_text and "Safari" in cause_text:
                actions.extend([
                    "Review mobile Safari checkout/session flow.",
                    "Check recent frontend releases affecting mobile Safari users.",
                    "Compare funnel steps for Mobile Safari against Chrome.",
                ])
            else:
                actions.append("Review conversion funnel changes for the affected segment.")
        elif kpi_name == "latency_ms":
            actions.extend([
                "Inspect regional latency, CDN routing, and browser-specific performance logs.",
                "Check backend response times and recent deployment windows.",
                "Compare Chrome performance against Safari and Firefox for the same region.",
            ])
        elif kpi_name == "revenue_per_session":
            if "Paid Search" in cause_text and "Enterprise" in cause_text:
                actions.extend([
                    "Review paid-search landing page quality and enterprise account purchase flow.",
                    "Check campaign targeting, discount logic, and high-value segment conversion path.",
                    "Compare Enterprise revenue per session against SMB and Mid-Market segments.",
                ])
            elif "Paid Search" in cause_text:
                actions.extend([
                    "Review paid-search landing page quality for the affected segment.",
                    "Check campaign targeting, landing page routing, and paid-search tracking.",
                    "Compare paid-search revenue per session against Organic and Email traffic.",
                ])
            elif "Enterprise" in cause_text:
                actions.extend([
                    "Review enterprise account purchase flow and pricing logic.",
                    "Check discount logic and high-value segment conversion path.",
                    "Compare Enterprise revenue per session against SMB and Mid-Market segments.",
                ])
            else:
                actions.extend([
                    "Review revenue per session drivers for the affected segment.",
                    "Check product mix, checkout path, pricing, and tracking for the suspected dimensions.",
                    "Compare affected segment revenue per session against adjacent segments.",
                ])
        else:
            actions.append(f"Review recent product, tracking, and campaign changes affecting {kpi_name}.")

        for cause in top_root_causes:
            if cause["recommended_action"] not in actions:
                actions.append(cause["recommended_action"])
        return actions[:max_actions]

    def _executive_summary(
        self,
        incident_date: str,
        kpi_name: str,
        severity: str,
        detector: str,
        top_root_causes: list[dict],
        actions: list[str],
    ) -> str:
        cause = top_root_causes[0] if top_root_causes else {"dimension_value": "the affected segment", "contribution_share": 0}
        contribution = cause["contribution_share"] * 100
        action = actions[0] if actions else "review the affected segment."
        movement = "excess latency" if self.kpi_directions.get(kpi_name) == "higher_is_bad" else "measured degradation"
        return (
            f"On {incident_date}, {kpi_name} showed a {severity.lower()} issue. "
            f"The {detector} detector flagged abnormal movement, and RCA identified "
            f"{cause['dimension_value']} as the dominant contributor, explaining "
            f"{contribution:.1f}% of {movement}. Recommended next step: {action}"
        )

    @staticmethod
    def _incident_id(date: str, kpi_name: str, detector: str) -> str:
        return f"INC-{str(date).replace('-', '')}-{kpi_name.upper().replace('_', '-')}-{detector.upper().replace('_', '-')}"

    @staticmethod
    def _severity_column(detector: str) -> str:
        if detector == "residual_anomaly":
            return "residual_severity"
        if detector == "zscore_anomaly":
            return "zscore_severity"
        if detector == "combined_anomaly":
            return "combined_severity"
        return "monitoring_status"

    @staticmethod
    def _max_severity(values: pd.Series) -> str:
        max_rank = values.map(SEVERITY_RANK).fillna(0).max()
        return {value: key for key, value in SEVERITY_RANK.items() if key in {"NORMAL", "WARNING", "CRITICAL"}}.get(int(max_rank), "NORMAL")

    def _render_markdown(self, payload: dict) -> str:
        lines = [
            "# KPI Incident Report",
            "",
            f"Generated at: `{payload['run_timestamp']}`",
            f"Detector used: `{payload['detector_used']}`",
            f"Incidents generated: **{payload['incidents_generated']}**",
            f"Highest severity: **{payload['highest_severity']}**",
            "",
            "## Executive Summary",
            "",
        ]
        if payload["incidents"]:
            lines.append(payload["incidents"][0]["executive_summary"])
        else:
            lines.append("No reportable incidents were generated.")

        lines.extend([
            "",
            "## Incident Table",
            "",
            "| Incident ID | Date | KPI | Severity | Confidence | Top Root Cause |",
            "|---|---:|---|---|---:|---|",
        ])
        for incident in payload["incidents"]:
            top_cause = incident["top_root_causes"][0]["dimension_value"] if incident["top_root_causes"] else ""
            lines.append(
                f"| {incident['incident_id']} | {incident['incident_date']} | "
                f"{incident['kpi_affected']} | {incident['severity']} | "
                f"{incident['confidence_label']} ({incident['confidence_score']:.3f}) | {top_cause} |"
            )

        for incident in payload["incidents"][:3]:
            lines.extend([
                "",
                f"## {incident['incident_id']}",
                "",
                incident["executive_summary"],
                "",
                "### Suspected Root Causes",
            ])
            for cause in incident["top_root_causes"]:
                lines.append(
                    f"- {cause['dimension_type']}: {cause['dimension_value']} "
                    f"({cause['contribution_share'] * 100:.1f}% contribution)"
                )
            lines.append("")
            lines.append("### Recommended Actions")
            for action in incident["recommended_actions"]:
                lines.append(f"- {action}")
            lines.append("")
            lines.append("### Supporting Metrics")
            lines.append(f"- Actual value summary: `{incident['actual_value_summary']}`")
            lines.append(f"- Expected value summary: `{incident['expected_value_summary']}`")
            lines.append(f"- Percent variance summary: `{incident['percent_variance_summary']}`")
            lines.append(f"- Anomaly rows: `{incident['anomaly_count']}`")

        lines.extend([
            "",
            "## Limitations",
            "",
        ])
        for limitation in payload["limitations"]:
            lines.append(f"- {limitation}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _render_html(markdown: str, payload: dict) -> str:
        escaped = html.escape(markdown)
        return (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<title>KPI Incident Report</title>"
            "<style>body{font-family:Arial,sans-serif;max-width:1100px;margin:32px auto;line-height:1.5;}"
            "pre{white-space:pre-wrap;background:#f8fafc;padding:20px;border:1px solid #e5e7eb;}"
            "</style></head><body>"
            f"<h1>KPI Incident Report</h1><p>Incidents generated: {payload['incidents_generated']}</p>"
            f"<pre>{escaped}</pre></body></html>"
        )

    @staticmethod
    def _write_history(incidents: list[dict], history_path: Path) -> None:
        rows = []
        for incident in incidents:
            top_cause = incident["top_root_causes"][0]["dimension_value"] if incident["top_root_causes"] else ""
            recommended_action = incident["recommended_actions"][0] if incident["recommended_actions"] else ""
            rows.append({
                "incident_id": incident["incident_id"],
                "date": incident["incident_date"],
                "kpi_affected": incident["kpi_affected"],
                "severity": incident["severity"],
                "confidence_label": incident["confidence_label"],
                "confidence_score": incident["confidence_score"],
                "top_root_cause": top_cause,
                "recommended_action": recommended_action,
                "detector_used": incident["detector_used"],
            })
        pd.DataFrame(rows).to_csv(history_path, index=False)
