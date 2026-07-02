from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.load_postgres import connect, resolve_settings


REQUIRED_SCHEMAS = ["raw", "analytics", "marts"]
REQUIRED_TABLES = [
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
    "marts.mart_data_quality_summary",
]


def _fetch_value(cursor, query: str) -> int:
    cursor.execute(query)
    value = cursor.fetchone()[0]
    return int(value)


def verify_warehouse() -> int:
    settings = resolve_settings()
    conn = connect(settings)
    failures: list[str] = []

    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = ANY(%s)",
                (REQUIRED_SCHEMAS,),
            )
            found_schemas = int(cursor.fetchone()[0])
            if found_schemas != len(REQUIRED_SCHEMAS):
                missing = [schema for schema in REQUIRED_SCHEMAS if _table_exists(cursor, schema, None) is False]
                failures.append(f"Missing schemas: {missing}")

            missing_tables = [table for table in REQUIRED_TABLES if not _table_exists(cursor, *table.split(".", 1))]
            if missing_tables:
                failures.append(f"Missing tables: {missing_tables}")

            counts = {
                table: _fetch_value(cursor, f"SELECT COUNT(*) FROM {table}")
                for table in REQUIRED_TABLES
                if _table_exists(cursor, *table.split(".", 1))
            }
            if any(count == 0 for count in counts.values()):
                empty = [table for table, count in counts.items() if count == 0]
                failures.append(f"Empty tables: {empty}")

            fact_key_checks = {
                "analytics.fact_kpi_daily": "date_key IS NULL OR kpi_key IS NULL OR region_key IS NULL OR device_key IS NULL OR browser_key IS NULL OR channel_key IS NULL OR business_segment_key IS NULL",
                "analytics.fact_kpi_monitoring": "date_key IS NULL OR kpi_key IS NULL OR region_key IS NULL OR device_key IS NULL OR browser_key IS NULL OR channel_key IS NULL OR business_segment_key IS NULL",
                "analytics.fact_kpi_anomalies": "date_key IS NULL OR kpi_key IS NULL OR region_key IS NULL OR device_key IS NULL OR browser_key IS NULL OR channel_key IS NULL OR business_segment_key IS NULL",
                "analytics.fact_rca_contributions": "analysis_date_key IS NULL OR kpi_key IS NULL",
                "analytics.fact_incidents": "incident_date_key IS NULL OR kpi_key IS NULL",
            }
            for table, clause in fact_key_checks.items():
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {clause}")
                null_count = int(cursor.fetchone()[0])
                if null_count:
                    failures.append(f"{table} has {null_count} null key rows")

            join_checks = {
                "analytics.fact_kpi_daily": [
                    "JOIN analytics.dim_date d ON d.date_key = f.date_key",
                    "JOIN analytics.dim_kpi k ON k.kpi_key = f.kpi_key",
                    "JOIN analytics.dim_region r ON r.region_key = f.region_key",
                    "JOIN analytics.dim_device dvc ON dvc.device_key = f.device_key",
                    "JOIN analytics.dim_browser b ON b.browser_key = f.browser_key",
                    "JOIN analytics.dim_channel c ON c.channel_key = f.channel_key",
                    "JOIN analytics.dim_business_segment s ON s.business_segment_key = f.business_segment_key",
                ],
                "analytics.fact_kpi_monitoring": [
                    "JOIN analytics.dim_date d ON d.date_key = f.date_key",
                    "JOIN analytics.dim_kpi k ON k.kpi_key = f.kpi_key",
                    "JOIN analytics.dim_region r ON r.region_key = f.region_key",
                    "JOIN analytics.dim_device dvc ON dvc.device_key = f.device_key",
                    "JOIN analytics.dim_browser b ON b.browser_key = f.browser_key",
                    "JOIN analytics.dim_channel c ON c.channel_key = f.channel_key",
                    "JOIN analytics.dim_business_segment s ON s.business_segment_key = f.business_segment_key",
                ],
                "analytics.fact_kpi_anomalies": [
                    "JOIN analytics.dim_date d ON d.date_key = f.date_key",
                    "JOIN analytics.dim_kpi k ON k.kpi_key = f.kpi_key",
                    "JOIN analytics.dim_region r ON r.region_key = f.region_key",
                    "JOIN analytics.dim_device dvc ON dvc.device_key = f.device_key",
                    "JOIN analytics.dim_browser b ON b.browser_key = f.browser_key",
                    "JOIN analytics.dim_channel c ON c.channel_key = f.channel_key",
                    "JOIN analytics.dim_business_segment s ON s.business_segment_key = f.business_segment_key",
                ],
                "analytics.fact_rca_contributions": [
                    "JOIN analytics.dim_date d ON d.date_key = f.analysis_date_key",
                    "JOIN analytics.dim_kpi k ON k.kpi_key = f.kpi_key",
                ],
                "analytics.fact_incidents": [
                    "JOIN analytics.dim_date d ON d.date_key = f.incident_date_key",
                    "JOIN analytics.dim_kpi k ON k.kpi_key = f.kpi_key",
                ],
            }
            for table, joins in join_checks.items():
                query = f"SELECT COUNT(*) FROM {table} f " + " ".join(joins) + " WHERE FALSE"
                # If any join alias were invalid, the query would fail; the zero-row count is enough for a syntactic check.
                cursor.execute(query)

    if failures:
        print("Warehouse verification FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Warehouse verification PASS")
    print(f"Schemas checked: {', '.join(REQUIRED_SCHEMAS)}")
    print(f"Tables checked: {len(REQUIRED_TABLES)}")
    return 0


def _table_exists(cursor, schema: str, table: str | None) -> bool:
    if table is None:
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = %s",
            (schema,),
        )
        return bool(cursor.fetchone()[0])
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s AND table_name = %s",
        (schema, table),
    )
    return bool(cursor.fetchone()[0])


def main() -> None:
    raise SystemExit(verify_warehouse())


if __name__ == "__main__":
    main()
