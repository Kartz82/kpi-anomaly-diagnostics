from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.kpi_monitoring import OUTPUT_COLUMNS, KPIMonitor


CONFIG_PATH = ROOT_DIR / "config/monitoring_config.yaml"


def _rows_for_group(
    kpi_name: str,
    values: list[float],
    region: str = "North America",
    device_type: str = "Desktop",
    browser: str = "Chrome",
    channel: str = "Organic",
    business_segment: str = "SMB",
) -> list[dict]:
    dates = pd.date_range("2026-01-01", periods=len(values), freq="D")
    return [
        {
            "date": date.strftime("%Y-%m-%d"),
            "kpi_name": kpi_name,
            "region": region,
            "device_type": device_type,
            "browser": browser,
            "channel": channel,
            "business_segment": business_segment,
            "impressions": 1000,
            "clicks": 100,
            "conversions": 10,
            "orders": 8,
            "revenue": 800.0,
            "latency_ms": 100.0,
            "kpi_value": value,
            "is_incident": False,
            "incident_id": "",
            "incident_type": "",
            "incident_description": "",
        }
        for date, value in zip(dates, values)
    ]


def test_output_contains_required_monitoring_columns():
    df = pd.DataFrame(_rows_for_group("conversion_rate", [0.1] * 10))

    monitoring = KPIMonitor(str(CONFIG_PATH)).build_monitoring_table(df)

    assert list(monitoring.columns) == OUTPUT_COLUMNS


def test_rolling_averages_are_calculated_within_kpi_dimension_groups():
    rows = _rows_for_group("conversion_rate", list(range(1, 10)), region="APAC")
    rows += _rows_for_group("conversion_rate", [100] * 9, region="EMEA")
    df = pd.DataFrame(rows)

    monitoring = KPIMonitor(str(CONFIG_PATH)).build_monitoring_table(df)
    apac_last = monitoring[
        (monitoring["region"] == "APAC") & (monitoring["date"] == "2026-01-09")
    ].iloc[0]

    assert apac_last["rolling_avg_7d"] == 6.0
    assert apac_last["rolling_avg_14d"] == 5.0


def test_moving_baseline_uses_prior_periods_without_current_day_leakage():
    df = pd.DataFrame(_rows_for_group("conversion_rate", list(range(1, 30))))

    monitoring = KPIMonitor(str(CONFIG_PATH)).build_monitoring_table(df)
    last = monitoring[monitoring["date"] == "2026-01-29"].iloc[0]

    assert last["moving_baseline"] == 14.5
    assert last["expected_value"] == 14.5
    assert last["rolling_avg_28d"] == 15.5


def test_variance_calculations_are_correct():
    values = [100.0] * 28 + [90.0]
    df = pd.DataFrame(_rows_for_group("conversion_rate", values))

    monitoring = KPIMonitor(str(CONFIG_PATH)).build_monitoring_table(df)
    last = monitoring[monitoring["date"] == "2026-01-29"].iloc[0]

    assert last["expected_value"] == 100.0
    assert last["absolute_variance"] == -10.0
    assert last["percent_variance"] == -0.10


def test_divide_by_zero_handling_does_not_crash():
    df = pd.DataFrame(_rows_for_group("conversion_rate", [0.0] * 29))

    monitoring = KPIMonitor(str(CONFIG_PATH)).build_monitoring_table(df)
    last = monitoring[monitoring["date"] == "2026-01-29"].iloc[0]

    assert pd.isna(last["percent_variance"])
    assert last["monitoring_status"] == "NORMAL"


def test_threshold_direction_works_for_lower_is_bad_kpis():
    df = pd.DataFrame(_rows_for_group("conversion_rate", [100.0] * 28 + [80.0]))

    monitoring = KPIMonitor(str(CONFIG_PATH)).build_monitoring_table(df)
    last = monitoring[monitoring["date"] == "2026-01-29"].iloc[0]

    assert last["threshold_direction"] == "lower_is_bad"
    assert bool(last["threshold_breached"]) is True
    assert last["monitoring_status"] == "CRITICAL"


def test_threshold_direction_works_for_higher_is_bad_kpis():
    df = pd.DataFrame(_rows_for_group("latency_ms", [100.0] * 28 + [131.0]))

    monitoring = KPIMonitor(str(CONFIG_PATH)).build_monitoring_table(df)
    last = monitoring[monitoring["date"] == "2026-01-29"].iloc[0]

    assert last["threshold_direction"] == "higher_is_bad"
    assert bool(last["threshold_breached"]) is True
    assert last["monitoring_status"] == "CRITICAL"


def test_monitoring_status_assigns_normal_warning_and_critical():
    rows = _rows_for_group("conversion_rate", [100.0] * 28 + [100.0], region="APAC")
    rows += _rows_for_group("conversion_rate", [100.0] * 28 + [90.0], region="EMEA")
    rows += _rows_for_group("conversion_rate", [100.0] * 28 + [80.0], region="North America")
    df = pd.DataFrame(rows)

    monitoring = KPIMonitor(str(CONFIG_PATH)).build_monitoring_table(df)
    last_day = monitoring[monitoring["date"] == "2026-01-29"]

    assert set(last_day["monitoring_status"]) == {"NORMAL", "WARNING", "CRITICAL"}


def test_monitoring_table_preserves_validated_input_grain():
    rows = _rows_for_group("conversion_rate", [0.1] * 10)
    rows += _rows_for_group("latency_ms", [200.0] * 10)
    df = pd.DataFrame(rows)

    monitoring = KPIMonitor(str(CONFIG_PATH)).build_monitoring_table(df)

    assert len(monitoring) == len(df)
    assert monitoring[
        [
            "date",
            "kpi_name",
            "region",
            "device_type",
            "browser",
            "channel",
            "business_segment",
        ]
    ].duplicated().sum() == 0
