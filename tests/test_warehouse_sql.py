from __future__ import annotations

from pathlib import Path

from scripts.load_postgres import DEFAULT_SETTINGS, resolve_settings


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_schema_sql_contains_expected_objects():
    schema = (ROOT_DIR / "sql/schema.sql").read_text()

    expected_tokens = [
        "CREATE SCHEMA IF NOT EXISTS raw",
        "CREATE SCHEMA IF NOT EXISTS analytics",
        "CREATE SCHEMA IF NOT EXISTS marts",
        "raw.raw_kpi_daily_metrics",
        "raw.raw_kpi_monitoring",
        "raw.raw_anomaly_results",
        "raw.raw_rca_contributions",
        "raw.raw_incident_history",
        "analytics.dim_date",
        "analytics.dim_kpi",
        "analytics.dim_region",
        "analytics.dim_device",
        "analytics.dim_browser",
        "analytics.dim_channel",
        "analytics.dim_business_segment",
        "analytics.fact_kpi_daily",
        "analytics.fact_kpi_monitoring",
        "analytics.fact_kpi_anomalies",
        "analytics.fact_rca_contributions",
        "analytics.fact_incidents",
        "marts.mart_kpi_health",
        "marts.mart_incident_summary",
    ]

    for token in expected_tokens:
        assert token in schema


def test_diagnostic_queries_include_core_business_examples():
    queries = (ROOT_DIR / "sql/diagnostic_queries.sql").read_text()

    expected_tokens = [
        "KPI health by day and KPI",
        "Anomaly count by KPI and severity",
        "Top RCA contributors by KPI/date",
        "Incident summary with confidence and severity",
        "Executive KPI health rollup",
        "Dimension drill-down query",
        "Mobile + APAC + Safari contribution to conversion degradation",
        "North America + Desktop + Chrome latency incident",
    ]

    for token in expected_tokens:
        assert token in queries


def test_load_script_exposes_clear_connection_defaults():
    settings = resolve_settings(env_path=ROOT_DIR / ".env.does-not-exist")

    for key, expected in DEFAULT_SETTINGS.items():
        if key == "POSTGRES_PORT":
            assert settings[key] == int(expected)
        else:
            assert settings[key] == expected

    load_script = (ROOT_DIR / "scripts/load_postgres.py").read_text()
    for token in ["POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "psycopg2-binary"]:
        assert token in load_script


def test_env_example_contains_required_variables():
    env_example = (ROOT_DIR / ".env.example").read_text()

    for token in [
        "POSTGRES_HOST=localhost",
        "POSTGRES_PORT=5432",
        "POSTGRES_DB=kpi_reliability",
        "POSTGRES_USER=kpi_user",
        "POSTGRES_PASSWORD=kpi_password",
    ]:
        assert token in env_example


def test_docker_compose_defines_postgres_service():
    compose = (ROOT_DIR / "docker-compose.yml").read_text()

    for token in [
        "image: postgres:16-alpine",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "${POSTGRES_PORT:-5432}:5432",
        "healthcheck",
        "postgres_data",
    ]:
        assert token in compose
