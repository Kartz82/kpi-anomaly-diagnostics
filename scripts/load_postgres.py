from __future__ import annotations

import argparse
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


DEFAULT_SETTINGS = {
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "kpi_reliability",
    "POSTGRES_USER": "kpi_user",
    "POSTGRES_PASSWORD": "kpi_password",
}

RAW_PATH = ROOT_DIR / "data/raw/kpi_daily_metrics.csv"
VALIDATED_PATH = ROOT_DIR / "data/processed/kpi_validated.csv"
MONITORING_PATH = ROOT_DIR / "data/processed/kpi_monitoring_table.csv"
ANOMALY_PATH = ROOT_DIR / "data/processed/anomaly_results.csv"
RCA_PATH = ROOT_DIR / "data/processed/rca_contribution_table.csv"
INCIDENT_HISTORY_PATH = ROOT_DIR / "data/reports/incident_history.csv"
LATEST_INCIDENT_PATH = ROOT_DIR / "data/reports/latest_incident.json"
DATA_QUALITY_REPORT_PATH = ROOT_DIR / "data/reports/data_quality_report.json"
SCHEMA_PATH = ROOT_DIR / "sql/schema.sql"


def load_env_file(path: Path | None = None) -> dict[str, str]:
    path = path or (ROOT_DIR / ".env")
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def resolve_settings(env_path: Path | None = None) -> dict[str, str | int]:
    settings = DEFAULT_SETTINGS.copy()
    settings.update(load_env_file(env_path))
    for key in DEFAULT_SETTINGS:
        if key in os.environ and os.environ[key]:
            settings[key] = os.environ[key]
    settings["POSTGRES_PORT"] = int(settings["POSTGRES_PORT"])
    return settings


def _connection_kwargs(settings: dict[str, str | int]) -> dict[str, object]:
    return {
        "host": settings["POSTGRES_HOST"],
        "port": settings["POSTGRES_PORT"],
        "dbname": settings["POSTGRES_DB"],
        "user": settings["POSTGRES_USER"],
        "password": settings["POSTGRES_PASSWORD"],
        "connect_timeout": 5,
    }


def _import_psycopg2():
    try:
        import psycopg2
        from psycopg2 import OperationalError
    except ImportError as exc:  # pragma: no cover - depends on local install
        raise SystemExit(
            "psycopg2-binary is required for PostgreSQL loads. "
            "Install project dependencies from requirements.txt first."
        ) from exc
    return psycopg2, OperationalError


def connect(settings: dict[str, str | int]):
    psycopg2, operational_error = _import_psycopg2()
    try:
        return psycopg2.connect(**_connection_kwargs(settings))
    except operational_error as exc:  # pragma: no cover - depends on local Docker
        raise SystemExit(
            "Unable to connect to PostgreSQL. Start the database with "
            "`docker compose up -d` and try again."
        ) from exc


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input file: {path}")
    return pd.read_csv(path, low_memory=False)


def read_latest_incident_lookup(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["incident_id", "anomaly_count", "executive_summary"])
    payload = json.loads(path.read_text())
    incidents = payload.get("incidents", [])
    if not incidents:
        return pd.DataFrame(columns=["incident_id", "anomaly_count", "executive_summary"])
    return pd.DataFrame(
        [
            {
                "incident_id": incident.get("incident_id"),
                "anomaly_count": incident.get("anomaly_count"),
                "executive_summary": incident.get("executive_summary"),
            }
            for incident in incidents
        ]
    )


def _date_key(series: pd.Series) -> pd.Series:
    dates = pd.to_datetime(series)
    return dates.dt.strftime("%Y%m%d").astype(int)


def build_dimensions(raw_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    dates = pd.to_datetime(raw_df["date"]).drop_duplicates().sort_values()
    date_df = pd.DataFrame(
        {
            "date_key": dates.dt.strftime("%Y%m%d").astype(int),
            "date_value": dates.dt.date,
            "year": dates.dt.year.astype(int),
            "quarter": dates.dt.quarter.astype(int),
            "month": dates.dt.month.astype(int),
            "day": dates.dt.day.astype(int),
            "day_of_week": dates.dt.dayofweek.astype(int),
            "day_name": dates.dt.day_name(),
            "is_weekend": dates.dt.dayofweek.isin([5, 6]),
        }
    )

    kpi_meta = {
        "conversion_rate": ("business_metric", "lower_is_bad", "ratio", "Conversion rate"),
        "click_through_rate": ("business_metric", "lower_is_bad", "ratio", "Click-through rate"),
        "average_order_value": ("business_metric", "lower_is_bad", "currency", "Average order value"),
        "latency_ms": ("performance_metric", "higher_is_bad", "milliseconds", "Latency in milliseconds"),
        "revenue_per_session": ("monetization_metric", "lower_is_bad", "currency", "Revenue per session"),
    }
    kpi_names = sorted(raw_df["kpi_name"].dropna().astype(str).unique().tolist())
    kpi_df = pd.DataFrame(
        [
            {
                "kpi_key": index + 1,
                "kpi_name": name,
                "kpi_family": kpi_meta.get(name, ("business_metric", "lower_is_bad", "ratio", name))[0],
                "direction": kpi_meta.get(name, ("business_metric", "lower_is_bad", "ratio", name))[1],
                "measure_unit": kpi_meta.get(name, ("business_metric", "lower_is_bad", "ratio", name))[2],
                "description": kpi_meta.get(name, ("business_metric", "lower_is_bad", "ratio", name))[3],
            }
            for index, name in enumerate(kpi_names)
        ]
    )

    def simple_dim(column: str, key_name: str) -> pd.DataFrame:
        values = sorted(raw_df[column].dropna().astype(str).unique().tolist())
        return pd.DataFrame({key_name: range(1, len(values) + 1), column: values})

    return {
        "dim_date": date_df,
        "dim_kpi": kpi_df,
        "dim_region": simple_dim("region", "region_key").rename(columns={"region": "region_name"}),
        "dim_device": simple_dim("device_type", "device_key"),
        "dim_browser": simple_dim("browser", "browser_key").rename(columns={"browser": "browser_name"}),
        "dim_channel": simple_dim("channel", "channel_key").rename(columns={"channel": "channel_name"}),
        "dim_business_segment": simple_dim("business_segment", "business_segment_key").rename(
            columns={"business_segment": "business_segment_name"}
        ),
    }


def _merge_keys(df: pd.DataFrame, dims: dict[str, pd.DataFrame]) -> pd.DataFrame:
    merged = df.copy()
    date_dim = dims["dim_date"][["date_key", "date_value"]].rename(columns={"date_value": "date"})
    merged["date"] = pd.to_datetime(merged["date"]).dt.date
    merged = merged.merge(date_dim, on="date", how="left")
    merged = merged.merge(dims["dim_kpi"][["kpi_key", "kpi_name"]], on="kpi_name", how="left")
    merged = merged.merge(dims["dim_region"][["region_key", "region_name"]], left_on="region", right_on="region_name", how="left")
    merged = merged.merge(dims["dim_device"][["device_key", "device_type"]], on="device_type", how="left")
    merged = merged.merge(dims["dim_browser"][["browser_key", "browser_name"]], left_on="browser", right_on="browser_name", how="left")
    merged = merged.merge(dims["dim_channel"][["channel_key", "channel_name"]], left_on="channel", right_on="channel_name", how="left")
    merged = merged.merge(
        dims["dim_business_segment"][["business_segment_key", "business_segment_name"]],
        left_on="business_segment",
        right_on="business_segment_name",
        how="left",
    )
    return merged


def build_facts(
    raw_df: pd.DataFrame,
    monitoring_df: pd.DataFrame,
    anomaly_df: pd.DataFrame,
    rca_df: pd.DataFrame,
    incident_df: pd.DataFrame,
    dims: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    raw_with_keys = _merge_keys(raw_df, dims)
    monitoring_with_keys = _merge_keys(monitoring_df.rename(columns={"date": "date"}), dims)
    anomaly_with_keys = _merge_keys(anomaly_df.rename(columns={"date": "date"}), dims)
    rca_with_keys = rca_df.copy()
    rca_with_keys["analysis_date"] = pd.to_datetime(rca_with_keys["analysis_date"]).dt.date
    rca_with_keys = rca_with_keys.merge(
        dims["dim_date"][["date_key", "date_value"]].rename(columns={"date_value": "analysis_date"}),
        on="analysis_date",
        how="left",
    )
    rca_with_keys = rca_with_keys.merge(
        dims["dim_kpi"][["kpi_key", "kpi_name"]],
        on="kpi_name",
        how="left",
    )
    incident_with_keys = incident_df.copy()
    incident_lookup = read_latest_incident_lookup(LATEST_INCIDENT_PATH)
    if not incident_lookup.empty:
        incident_with_keys = incident_with_keys.merge(incident_lookup, on="incident_id", how="left")
    if "anomaly_count" not in incident_with_keys.columns:
        incident_with_keys["anomaly_count"] = 1
    if "executive_summary" not in incident_with_keys.columns:
        incident_with_keys["executive_summary"] = ""
    incident_with_keys["anomaly_count"] = incident_with_keys["anomaly_count"].fillna(1).astype(int)
    incident_with_keys["executive_summary"] = incident_with_keys["executive_summary"].fillna("")
    incident_with_keys["date"] = pd.to_datetime(incident_with_keys["date"]).dt.date
    incident_with_keys = incident_with_keys.merge(
        dims["dim_date"][["date_key", "date_value"]].rename(columns={"date_value": "date"}),
        on="date",
        how="left",
    )

    fact_daily = raw_with_keys[
        [
            "date_key",
            "kpi_key",
            "region_key",
            "device_key",
            "browser_key",
            "channel_key",
            "business_segment_key",
            "impressions",
            "clicks",
            "conversions",
            "orders",
            "revenue",
            "latency_ms",
            "kpi_value",
            "is_incident",
            "incident_id",
            "incident_type",
            "incident_description",
        ]
    ].copy()

    fact_monitoring = monitoring_with_keys[
        [
            "date_key",
            "kpi_key",
            "region_key",
            "device_key",
            "browser_key",
            "channel_key",
            "business_segment_key",
            "actual_value",
            "rolling_avg_7d",
            "rolling_avg_14d",
            "rolling_avg_28d",
            "moving_baseline",
            "expected_value",
            "absolute_variance",
            "percent_variance",
            "threshold_value",
            "threshold_direction",
            "threshold_breached",
            "monitoring_status",
        ]
    ].copy()

    fact_anomalies = anomaly_with_keys[
        [
            "date_key",
            "kpi_key",
            "region_key",
            "device_key",
            "browser_key",
            "channel_key",
            "business_segment_key",
            "actual_value",
            "expected_value",
            "moving_baseline",
            "percent_variance",
            "monitoring_status",
            "threshold_breached",
            "z_score",
            "zscore_anomaly",
            "zscore_severity",
            "predicted_value",
            "residual",
            "residual_percent",
            "residual_anomaly",
            "residual_severity",
            "combined_anomaly",
            "combined_severity",
            "is_incident",
            "incident_id",
            "incident_type",
            "incident_description",
        ]
    ].copy()

    fact_rca = rca_with_keys[
        [
            "date_key",
            "kpi_key",
            "detector_used",
            "dimension_type",
            "dimension_value",
            "actual_value_sum_or_avg",
            "expected_value_sum_or_avg",
            "degradation_amount",
            "contribution_share",
            "contribution_rank",
            "anomaly_count",
            "severity_max",
            "recommended_action",
        ]
    ].rename(columns={"date_key": "analysis_date_key"})

    fact_incidents = incident_with_keys[
        [
            "incident_id",
            "date_key",
            "kpi_affected",
            "severity",
            "confidence_score",
            "confidence_label",
            "detector_used",
            "anomaly_count",
            "top_root_cause",
            "recommended_action",
            "executive_summary",
        ]
    ].rename(columns={"date_key": "incident_date_key", "kpi_affected": "kpi_name"})
    fact_incidents = fact_incidents.merge(
        dims["dim_kpi"][["kpi_key", "kpi_name"]], on="kpi_name", how="left"
    ).drop(columns=["kpi_name"])

    return {
        "fact_kpi_daily": fact_daily,
        "fact_kpi_monitoring": fact_monitoring,
        "fact_kpi_anomalies": fact_anomalies,
        "fact_rca_contributions": fact_rca,
        "fact_incidents": fact_incidents,
    }


def build_marts(
    facts: dict[str, pd.DataFrame],
    data_quality_report: dict,
    dims: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    monitoring = facts["fact_kpi_monitoring"].copy()
    monitoring_health = (
        monitoring.groupby(["date_key", "kpi_key"], as_index=False)
        .agg(
            monitored_rows=("threshold_breached", "size"),
            normal_rows=("monitoring_status", lambda s: int((s == "NORMAL").sum())),
            warning_rows=("monitoring_status", lambda s: int((s == "WARNING").sum())),
            critical_rows=("monitoring_status", lambda s: int((s == "CRITICAL").sum())),
            breach_rows=("threshold_breached", lambda s: int(s.astype(bool).sum())),
            avg_actual_value=("actual_value", "mean"),
            avg_expected_value=("expected_value", "mean"),
            avg_percent_variance=("percent_variance", "mean"),
            max_abs_percent_variance=("percent_variance", lambda s: float(s.abs().max())),
        )
    )
    monitoring_health["avg_expected_value"] = monitoring_health["avg_expected_value"].fillna(0.0)
    monitoring_health["avg_percent_variance"] = monitoring_health["avg_percent_variance"].fillna(0.0)
    monitoring_health["max_abs_percent_variance"] = monitoring_health["max_abs_percent_variance"].fillna(0.0)
    monitoring_health["health_score"] = (
        100
        - (
            monitoring_health["warning_rows"] * 0.5
            + monitoring_health["critical_rows"] * 1.5
        )
        / monitoring_health["monitored_rows"].replace(0, 1)
        * 100
    ).clip(lower=0, upper=100)
    mart_kpi_health = monitoring_health[
        [
            "date_key",
            "kpi_key",
            "monitored_rows",
            "normal_rows",
            "warning_rows",
            "critical_rows",
            "breach_rows",
            "avg_actual_value",
            "avg_expected_value",
            "avg_percent_variance",
            "max_abs_percent_variance",
            "health_score",
        ]
    ].copy()

    fact_incidents = facts["fact_incidents"].copy()
    mart_incident_summary = fact_incidents[
        [
            "incident_id",
            "incident_date_key",
            "kpi_key",
            "severity",
            "confidence_label",
            "confidence_score",
            "detector_used",
            "anomaly_count",
            "top_root_cause",
            "recommended_action",
            "executive_summary",
        ]
    ].copy()

    dq = data_quality_report
    checks = dq.get("checks", {})
    def check_status(name: str) -> str:
        return "PASS" if checks.get(name, {}).get("passed") else "FAIL"

    mart_data_quality_summary = pd.DataFrame(
        [
            {
                "run_timestamp": dq.get(
                    "run_timestamp",
                    datetime.now(timezone.utc).isoformat(),
                ),
                "status": dq.get("status", "UNKNOWN"),
                "health_score": int(dq.get("health_score", 0)),
                "schema_status": check_status("schema"),
                "null_issue_count": int(checks.get("nulls", {}).get("null_count", 0)),
                "duplicate_issue_count": int(checks.get("duplicates", {}).get("duplicate_count", 0)),
                "freshness_status": check_status("freshness"),
                "completeness_status": check_status("completeness"),
                "volume_status": check_status("volume"),
                "overall_issue_count": int(len(dq.get("issues", []))),
            }
        ]
    )

    return {
        "mart_kpi_health": mart_kpi_health,
        "mart_incident_summary": mart_incident_summary,
        "mart_data_quality_summary": mart_data_quality_summary,
    }


def dataframe_to_copy_sql(table: str, columns: list[str]) -> str:
    cols = ", ".join(columns)
    return f"COPY {table} ({cols}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)"


def load_dataframe(cursor, table: str, df: pd.DataFrame) -> int:
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    cursor.copy_expert(dataframe_to_copy_sql(table, list(df.columns)), buffer)
    return len(df)


def truncate_tables(cursor) -> None:
    tables = [
        "marts.mart_data_quality_summary",
        "marts.mart_incident_summary",
        "marts.mart_kpi_health",
        "analytics.fact_incidents",
        "analytics.fact_rca_contributions",
        "analytics.fact_kpi_anomalies",
        "analytics.fact_kpi_monitoring",
        "analytics.fact_kpi_daily",
        "analytics.dim_business_segment",
        "analytics.dim_channel",
        "analytics.dim_browser",
        "analytics.dim_device",
        "analytics.dim_region",
        "analytics.dim_kpi",
        "analytics.dim_date",
        "raw.raw_incident_history",
        "raw.raw_rca_contributions",
        "raw.raw_anomaly_results",
        "raw.raw_kpi_monitoring",
        "raw.raw_kpi_daily_metrics",
    ]
    cursor.execute(f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE;")


def load_warehouse(settings: dict[str, str | int]) -> dict[str, int]:
    conn = connect(settings)
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(SCHEMA_PATH.read_text())
                truncate_tables(cursor)

                raw_df = read_csv(RAW_PATH)
                validated_df = read_csv(VALIDATED_PATH)
                monitoring_df = read_csv(MONITORING_PATH)
                anomaly_df = read_csv(ANOMALY_PATH)
                rca_df = read_csv(RCA_PATH)
                incident_df = read_csv(INCIDENT_HISTORY_PATH)
                dq_report = json.loads(DATA_QUALITY_REPORT_PATH.read_text())

                dimensions = build_dimensions(raw_df)
                facts = build_facts(raw_df, monitoring_df, anomaly_df, rca_df, incident_df, dimensions)
                marts = build_marts(facts, dq_report, dimensions)

                raw_counts = {
                    "raw.raw_kpi_daily_metrics": load_dataframe(cursor, "raw.raw_kpi_daily_metrics", raw_df),
                    "raw.raw_kpi_monitoring": load_dataframe(cursor, "raw.raw_kpi_monitoring", monitoring_df),
                    "raw.raw_anomaly_results": load_dataframe(cursor, "raw.raw_anomaly_results", anomaly_df),
                    "raw.raw_rca_contributions": load_dataframe(cursor, "raw.raw_rca_contributions", rca_df),
                    "raw.raw_incident_history": load_dataframe(cursor, "raw.raw_incident_history", incident_df),
                }

                dimension_counts = {
                    "analytics.dim_date": load_dataframe(cursor, "analytics.dim_date", dimensions["dim_date"]),
                    "analytics.dim_kpi": load_dataframe(cursor, "analytics.dim_kpi", dimensions["dim_kpi"]),
                    "analytics.dim_region": load_dataframe(cursor, "analytics.dim_region", dimensions["dim_region"]),
                    "analytics.dim_device": load_dataframe(cursor, "analytics.dim_device", dimensions["dim_device"]),
                    "analytics.dim_browser": load_dataframe(cursor, "analytics.dim_browser", dimensions["dim_browser"]),
                    "analytics.dim_channel": load_dataframe(cursor, "analytics.dim_channel", dimensions["dim_channel"]),
                    "analytics.dim_business_segment": load_dataframe(cursor, "analytics.dim_business_segment", dimensions["dim_business_segment"]),
                }

                fact_counts = {
                    "analytics.fact_kpi_daily": load_dataframe(cursor, "analytics.fact_kpi_daily", facts["fact_kpi_daily"]),
                    "analytics.fact_kpi_monitoring": load_dataframe(cursor, "analytics.fact_kpi_monitoring", facts["fact_kpi_monitoring"]),
                    "analytics.fact_kpi_anomalies": load_dataframe(cursor, "analytics.fact_kpi_anomalies", facts["fact_kpi_anomalies"]),
                    "analytics.fact_rca_contributions": load_dataframe(cursor, "analytics.fact_rca_contributions", facts["fact_rca_contributions"]),
                    "analytics.fact_incidents": load_dataframe(cursor, "analytics.fact_incidents", facts["fact_incidents"]),
                }

                mart_counts = {
                    "marts.mart_kpi_health": load_dataframe(cursor, "marts.mart_kpi_health", marts["mart_kpi_health"]),
                    "marts.mart_incident_summary": load_dataframe(cursor, "marts.mart_incident_summary", marts["mart_incident_summary"]),
                    "marts.mart_data_quality_summary": load_dataframe(cursor, "marts.mart_data_quality_summary", marts["mart_data_quality_summary"]),
                }

        return {
            **raw_counts,
            **dimension_counts,
            **fact_counts,
            **mart_counts,
            "validated_rows_read": len(validated_df),
        }
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Load Phase 6A warehouse tables into PostgreSQL.")
    args = parser.parse_args()
    settings = resolve_settings()
    counts = load_warehouse(settings)

    print("PostgreSQL warehouse load complete")
    print(f"Connection target: {settings['POSTGRES_HOST']}:{settings['POSTGRES_PORT']}/{settings['POSTGRES_DB']}")
    print(f"Validated rows read: {counts['validated_rows_read']:,}")
    for table, count in counts.items():
        if table == "validated_rows_read":
            continue
        print(f"{table}: {count:,}")


if __name__ == "__main__":
    main()
