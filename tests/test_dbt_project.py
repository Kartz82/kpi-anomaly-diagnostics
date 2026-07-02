from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DBT_DIR = ROOT_DIR / "dbt"


def test_dbt_project_files_exist():
    expected = [
        DBT_DIR / "dbt_project.yml",
        DBT_DIR / "profiles.example.yml",
        DBT_DIR / "models" / "sources.yml",
        DBT_DIR / "models" / "staging" / "staging.yml",
        DBT_DIR / "models" / "intermediate" / "intermediate.yml",
        DBT_DIR / "models" / "marts" / "marts.yml",
        DBT_DIR / "macros" / "generate_schema_name.sql",
        ROOT_DIR / "scripts" / "run_dbt.py",
    ]

    for path in expected:
        assert path.exists(), path


def test_dbt_models_cover_expected_layers():
    expected_models = [
        "stg_kpi_daily_metrics.sql",
        "stg_kpi_monitoring.sql",
        "stg_anomaly_results.sql",
        "stg_rca_contributions.sql",
        "stg_incident_history.sql",
        "int_kpi_monitoring.sql",
        "int_anomaly_events.sql",
        "int_rca_contributions.sql",
        "int_incident_enriched.sql",
        "dim_date.sql",
        "dim_kpi.sql",
        "dim_region.sql",
        "dim_device.sql",
        "dim_browser.sql",
        "dim_channel.sql",
        "dim_business_segment.sql",
        "fact_kpi_daily.sql",
        "fact_kpi_monitoring.sql",
        "fact_kpi_anomalies.sql",
        "fact_rca_contributions.sql",
        "fact_incidents.sql",
        "mart_kpi_health.sql",
        "mart_incident_summary.sql",
        "mart_root_cause_summary.sql",
    ]

    for model in expected_models:
        assert any(DBT_DIR.rglob(model)), model


def test_dbt_schema_files_include_expected_tests():
    source_yml = (DBT_DIR / "models" / "sources.yml").read_text()
    staging_yml = (DBT_DIR / "models" / "staging" / "staging.yml").read_text()
    intermediate_yml = (DBT_DIR / "models" / "intermediate" / "intermediate.yml").read_text()
    marts_yml = (DBT_DIR / "models" / "marts" / "marts.yml").read_text()
    macros = (DBT_DIR / "macros" / "generic_tests.sql").read_text()

    for token in [
        "accepted_values",
        "not_null",
        "unique_combination_of_columns",
        "assert_contribution_share_bounds",
        "assert_incident_confidence_bounds",
        "relationships",
        "unique",
    ]:
        assert token in source_yml or token in staging_yml or token in intermediate_yml or token in marts_yml or token in macros


def test_dbt_project_and_profile_defaults():
    project = (DBT_DIR / "dbt_project.yml").read_text()
    profile = (DBT_DIR / "profiles.example.yml").read_text()

    for token in [
        "name: kpi_reliability_dbt",
        "dbt_staging",
        "dbt_intermediate",
        "dbt_marts",
        "profile: kpi_reliability_dbt",
        "type: postgres",
        "host: localhost",
        "port: 5432",
        "dbname: kpi_reliability",
        "user: kpi_user",
        "password: kpi_password",
    ]:
        assert token in project or token in profile


def test_run_dbt_script_mentions_failure_modes():
    script = (ROOT_DIR / "scripts" / "run_dbt.py").read_text()
    for token in [
        "dbt is not installed",
        "DBT_PROFILES_DIR",
        "dbt debug",
        "dbt run",
        "dbt test",
    ]:
        assert token in script
