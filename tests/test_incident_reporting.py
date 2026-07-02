from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.run_pipeline import run_phase_1_pipeline
from src.core.incident_reporting import IncidentReporter


CONFIG_PATH = ROOT_DIR / "config/monitoring_config.yaml"


def _anomaly_row(date: str, kpi_name: str, severity: str = "CRITICAL") -> dict:
    return {
        "date": date,
        "kpi_name": kpi_name,
        "region": "APAC" if kpi_name == "conversion_rate" else "North America",
        "device_type": "Mobile" if kpi_name == "conversion_rate" else "Desktop",
        "browser": "Safari" if kpi_name == "conversion_rate" else "Chrome",
        "channel": "Paid Search" if kpi_name == "revenue_per_session" else "Organic",
        "business_segment": "Enterprise" if kpi_name == "revenue_per_session" else "SMB",
        "actual_value": 70.0,
        "expected_value": 100.0,
        "moving_baseline": 100.0,
        "percent_variance": -0.30 if kpi_name != "latency_ms" else 0.45,
        "monitoring_status": severity,
        "threshold_breached": True,
        "z_score": 4.0,
        "zscore_anomaly": True,
        "zscore_severity": severity,
        "predicted_value": 100.0,
        "residual": -30.0 if kpi_name != "latency_ms" else 45.0,
        "residual_percent": -0.30 if kpi_name != "latency_ms" else 0.45,
        "residual_anomaly": True,
        "residual_severity": severity,
        "combined_anomaly": True,
        "combined_severity": severity,
        "is_incident": True,
        "incident_id": "",
        "incident_type": "",
        "incident_description": "",
    }


def _rca_row(date: str, kpi_name: str, dimension_value: str, share: float = 1.0) -> dict:
    return {
        "analysis_date": date,
        "kpi_name": kpi_name,
        "detector_used": "residual_anomaly",
        "dimension_type": "region_device_browser",
        "dimension_value": dimension_value,
        "actual_value_sum_or_avg": 70.0,
        "expected_value_sum_or_avg": 100.0,
        "degradation_amount": 30.0,
        "contribution_share": share,
        "contribution_rank": 1,
        "anomaly_count": 1,
        "severity_max": "CRITICAL",
        "recommended_action": "Review affected segment.",
    }


def _contexts():
    return (
        {"best_detector": "ml_residual", "best_detector_f1_score": 0.55, "residual_model_used": "numpy_ridge"},
        {"top_root_cause_statements": []},
        {"status": "PASS", "health_score": 100},
        {"warning_count": 5, "critical_count": 2},
    )


def test_incident_report_creates_required_json_structure(tmp_path):
    reporter = IncidentReporter(str(CONFIG_PATH))
    anoms = pd.DataFrame([_anomaly_row("2026-06-06", "conversion_rate")])
    rca = pd.DataFrame([_rca_row("2026-06-06", "conversion_rate", "APAC + Mobile + Safari")])
    model, root, dq, mon = _contexts()

    payload = reporter.generate_reports(
        anoms, rca, model, root, dq, mon,
        json_path=tmp_path / "incident.json",
        markdown_path=tmp_path / "incident.md",
        html_path=tmp_path / "incident.html",
        history_path=tmp_path / "history.csv",
    )

    assert payload["incidents_generated"] == 1
    assert payload["detector_used"] == "residual_anomaly"
    assert payload["incidents"][0]["kpi_affected"] == "conversion_rate"
    assert (tmp_path / "incident.json").exists()


def test_incidents_are_grouped_by_kpi_and_date():
    reporter = IncidentReporter(str(CONFIG_PATH))
    anoms = pd.DataFrame([
        _anomaly_row("2026-06-06", "conversion_rate"),
        _anomaly_row("2026-06-06", "conversion_rate"),
        _anomaly_row("2026-05-18", "latency_ms"),
    ])
    rca = pd.DataFrame([
        _rca_row("2026-06-06", "conversion_rate", "APAC + Mobile + Safari"),
        _rca_row("2026-05-18", "latency_ms", "North America + Desktop + Chrome"),
    ])
    model, root, dq, mon = _contexts()

    incidents = reporter.build_incidents(anoms, rca, model, root, dq, mon)

    assert len(incidents) == 2
    assert sorted(incident["anomaly_count"] for incident in incidents) == [1, 2]


def test_severity_assignment_and_confidence_bounds():
    reporter = IncidentReporter(str(CONFIG_PATH))
    anoms = pd.DataFrame([_anomaly_row("2026-05-18", "latency_ms", severity="CRITICAL")])
    rca = pd.DataFrame([_rca_row("2026-05-18", "latency_ms", "North America + Desktop + Chrome")])
    model, root, dq, mon = _contexts()

    incident = reporter.build_incidents(anoms, rca, model, root, dq, mon)[0]

    assert incident["severity"] == "CRITICAL"
    assert 0 <= incident["confidence_score"] <= 1


def test_confidence_label_maps_correctly():
    reporter = IncidentReporter(str(CONFIG_PATH))

    assert reporter._confidence_label(0.80) == "High"
    assert reporter._confidence_label(0.75) == "Medium"
    assert reporter._confidence_label(0.55) == "Medium"
    assert reporter._confidence_label(0.54) == "Low"


def test_recommended_actions_cover_core_kpis():
    reporter = IncidentReporter(str(CONFIG_PATH))

    conversion = reporter._recommended_actions(
        "conversion_rate",
        [{"dimension_value": "APAC + Mobile + Safari", "recommended_action": "Review affected segment."}],
        3,
    )
    latency = reporter._recommended_actions(
        "latency_ms",
        [{"dimension_value": "North America + Desktop + Chrome", "recommended_action": "Review affected segment."}],
        3,
    )
    revenue = reporter._recommended_actions(
        "revenue_per_session",
        [{"dimension_value": "Paid Search + Enterprise", "recommended_action": "Review affected segment."}],
        3,
    )

    assert any("mobile Safari" in action for action in conversion)
    assert any("CDN" in action for action in latency)
    assert any("paid-search" in action for action in revenue)


def test_revenue_recommendations_match_actual_dimensions():
    reporter = IncidentReporter(str(CONFIG_PATH))

    generic = reporter._recommended_actions(
        "revenue_per_session",
        [{"dimension_value": "North America + Mobile + Chrome", "recommended_action": "Review affected segment."}],
        3,
    )
    paid_search = reporter._recommended_actions(
        "revenue_per_session",
        [{"dimension_value": "North America + Mobile + Chrome + Paid Search + SMB", "recommended_action": "Review affected segment."}],
        3,
    )

    assert not any("Enterprise" in action for action in generic)
    assert not any("paid-search" in action for action in generic)
    assert any("paid-search" in action for action in paid_search)
    assert not any("enterprise account" in action for action in paid_search)


def test_executive_summary_contains_kpi_date_root_cause_and_recommendation():
    reporter = IncidentReporter(str(CONFIG_PATH))
    summary = reporter._executive_summary(
        "2026-06-06",
        "conversion_rate",
        "CRITICAL",
        "residual_anomaly",
        [{"dimension_value": "APAC + Mobile + Safari", "contribution_share": 1.0}],
        ["Review mobile Safari checkout/session flow."],
    )

    assert "2026-06-06" in summary
    assert "conversion_rate" in summary
    assert "APAC + Mobile + Safari" in summary
    assert "Review mobile Safari" in summary


def test_markdown_html_and_history_are_generated(tmp_path):
    reporter = IncidentReporter(str(CONFIG_PATH))
    incident = {
        "incident_id": "INC-1",
        "incident_date": "2026-06-06",
        "kpi_affected": "conversion_rate",
        "severity": "CRITICAL",
        "confidence_score": 0.9,
        "confidence_label": "High",
        "detector_used": "residual_anomaly",
        "actual_value_summary": 0.1,
        "expected_value_summary": 0.2,
        "percent_variance_summary": -0.5,
        "anomaly_count": 3,
        "top_root_causes": [{"dimension_value": "APAC + Mobile + Safari", "dimension_type": "region_device_browser", "contribution_share": 1.0}],
        "recommended_actions": ["Review mobile Safari checkout/session flow."],
        "executive_summary": "Summary text",
        "supporting_metrics": {},
        "data_quality_context": {},
        "model_context": {},
    }

    payload = reporter.write_outputs(
        [incident],
        json_path=tmp_path / "incident.json",
        markdown_path=tmp_path / "incident.md",
        html_path=tmp_path / "incident.html",
        history_path=tmp_path / "history.csv",
    )

    assert payload["incidents_generated"] == 1
    assert (tmp_path / "incident.md").exists()
    assert (tmp_path / "incident.html").exists()
    assert pd.read_csv(tmp_path / "history.csv").shape[0] == 1


def test_pipeline_creates_incident_outputs():
    summary = run_phase_1_pipeline(regenerate=True)

    assert summary["incidents_generated"] > 0
    assert Path(summary["latest_incident_json_path"]).exists()
    assert Path(summary["latest_incident_md_path"]).exists()
    assert Path(summary["latest_incident_html_path"]).exists()
    assert Path(summary["incident_history_path"]).exists()


def test_incident_reporting_does_not_require_external_services():
    reporter = IncidentReporter(str(CONFIG_PATH))

    assert reporter.incident_config["default_detector"] == "residual_anomaly"
