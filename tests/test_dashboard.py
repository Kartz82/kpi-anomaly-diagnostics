from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = ROOT_DIR / "dashboards"


def test_dashboard_files_exist():
    for path in [
        DASHBOARD_DIR / "streamlit_app.py",
        DASHBOARD_DIR / "README.md",
        DASHBOARD_DIR / "screenshots" / "README.md",
    ]:
        assert path.exists(), path


def test_dashboard_source_references_expected_inputs_and_sections():
    source = (DASHBOARD_DIR / "streamlit_app.py").read_text()

    required_tokens = [
        "Executive Overview",
        "KPI Health",
        "Anomaly Timeline",
        "Root Cause Explorer",
        "Data Quality",
        "Incident Center",
        "data/processed/kpi_monitoring_table.csv",
        "data/processed/anomaly_results.csv",
        "data/processed/rca_contribution_table.csv",
        "data/reports/data_quality_report.json",
        "data/reports/kpi_monitoring_summary.json",
        "data/reports/model_evaluation.csv",
        "data/reports/model_comparison.json",
        "data/reports/root_cause_summary.json",
        "data/reports/latest_incident.json",
        "data/reports/incident_history.csv",
        "streamlit",
    ]

    for token in required_tokens:
        assert token in source, token


def test_dashboard_is_local_file_first_and_does_not_require_postgres_by_default():
    source = (DASHBOARD_DIR / "streamlit_app.py").read_text()
    readme = (DASHBOARD_DIR / "README.md").read_text()

    for token in [
        "PostgreSQL is not required for normal dashboard usage.",
        "local-file first",
        "dashboard reads local CSV and JSON outputs by default",
    ]:
        assert token in readme or token in source

    assert "psycopg2" not in source


def test_dashboard_readme_and_screenshot_guidance_are_present():
    readme = (DASHBOARD_DIR / "README.md").read_text()
    screenshots = (DASHBOARD_DIR / "screenshots" / "README.md").read_text()
    requirements = (ROOT_DIR / "requirements.txt").read_text()

    for token in [
        "streamlit run dashboards/streamlit_app.py",
        "Executive Overview",
        "KPI Health",
        "Anomaly Timeline",
        "Root Cause Explorer",
        "Data Quality",
        "Incident Center",
    ]:
        assert token in readme

    for token in [
        "executive_overview.png",
        "kpi_health.png",
        "anomaly_timeline.png",
        "root_cause_explorer.png",
        "data_quality.png",
        "incident_center.png",
    ]:
        assert token in screenshots

    assert "streamlit" in requirements
