from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.run_pipeline import run_phase_1_pipeline
from src.core.root_cause import RCA_OUTPUT_COLUMNS, RootCauseAnalyzer


CONFIG_PATH = ROOT_DIR / "config/monitoring_config.yaml"


def _row(
    date: str,
    kpi_name: str,
    actual: float,
    expected: float,
    region: str = "APAC",
    device_type: str = "Mobile",
    browser: str = "Safari",
    channel: str = "Organic",
    business_segment: str = "SMB",
    residual_anomaly: bool = True,
    zscore_anomaly: bool = False,
    severity: str = "CRITICAL",
) -> dict:
    percent_variance = (actual - expected) / expected if expected else pd.NA
    return {
        "date": date,
        "kpi_name": kpi_name,
        "region": region,
        "device_type": device_type,
        "browser": browser,
        "channel": channel,
        "business_segment": business_segment,
        "actual_value": actual,
        "expected_value": expected,
        "moving_baseline": expected,
        "percent_variance": percent_variance,
        "monitoring_status": severity,
        "threshold_breached": residual_anomaly,
        "z_score": 4.5 if zscore_anomaly else 0.0,
        "zscore_anomaly": zscore_anomaly,
        "zscore_severity": severity if zscore_anomaly else "NORMAL",
        "predicted_value": expected,
        "residual": actual - expected,
        "residual_percent": percent_variance,
        "residual_anomaly": residual_anomaly,
        "residual_severity": severity if residual_anomaly else "NORMAL",
        "combined_anomaly": residual_anomaly or zscore_anomaly,
        "combined_severity": severity if (residual_anomaly or zscore_anomaly) else "NORMAL",
        "is_incident": residual_anomaly,
        "incident_id": "",
        "incident_type": "",
        "incident_description": "",
    }


def test_rca_uses_residual_anomaly_by_default():
    df = pd.DataFrame([
        _row("2026-01-01", "conversion_rate", actual=80, expected=100, residual_anomaly=True),
        _row("2026-01-01", "conversion_rate", actual=50, expected=100, residual_anomaly=False, zscore_anomaly=True),
    ])

    table = RootCauseAnalyzer(config_path=str(CONFIG_PATH)).build_contribution_table(df)

    assert set(table["detector_used"]) == {"residual_anomaly"}
    assert table["anomaly_count"].max() == 1


def test_rca_accepts_another_detector_column():
    df = pd.DataFrame([
        _row("2026-01-01", "conversion_rate", actual=80, expected=100, residual_anomaly=False, zscore_anomaly=True),
    ])

    table = RootCauseAnalyzer(config_path=str(CONFIG_PATH)).build_contribution_table(
        df,
        detector="zscore_anomaly",
    )

    assert not table.empty
    assert set(table["detector_used"]) == {"zscore_anomaly"}


def test_lower_is_bad_degradation_is_calculated_correctly():
    row = pd.Series({"kpi_name": "conversion_rate", "actual_value": 80, "expected_value": 100})

    amount = RootCauseAnalyzer(config_path=str(CONFIG_PATH))._degradation_amount(row)

    assert amount == 20


def test_higher_is_bad_degradation_is_calculated_correctly():
    row = pd.Series({"kpi_name": "latency_ms", "actual_value": 130, "expected_value": 100})

    amount = RootCauseAnalyzer(config_path=str(CONFIG_PATH))._degradation_amount(row)

    assert amount == 30


def test_non_degrading_movement_does_not_create_false_contribution():
    df = pd.DataFrame([
        _row("2026-01-01", "conversion_rate", actual=120, expected=100, residual_anomaly=True),
    ])

    table = RootCauseAnalyzer(config_path=str(CONFIG_PATH)).build_contribution_table(df)

    assert table.empty


def test_contribution_shares_sum_to_one_within_analysis_group():
    df = pd.DataFrame([
        _row("2026-01-01", "conversion_rate", actual=80, expected=100, region="APAC"),
        _row("2026-01-01", "conversion_rate", actual=90, expected=100, region="EMEA"),
    ])

    table = RootCauseAnalyzer(config_path=str(CONFIG_PATH)).build_contribution_table(df)
    region_rows = table[table["dimension_type"] == "region"]

    assert round(region_rows["contribution_share"].sum(), 6) == 1.0


def test_contribution_ranking_and_required_columns_work():
    df = pd.DataFrame([
        _row("2026-01-01", "conversion_rate", actual=70, expected=100, region="APAC"),
        _row("2026-01-01", "conversion_rate", actual=90, expected=100, region="EMEA"),
    ])

    table = RootCauseAnalyzer(config_path=str(CONFIG_PATH)).build_contribution_table(df)
    region_rows = table[table["dimension_type"] == "region"].sort_values("contribution_rank")

    assert list(table.columns) == RCA_OUTPUT_COLUMNS
    assert region_rows.iloc[0]["dimension_value"] == "APAC"
    assert region_rows.iloc[0]["contribution_rank"] == 1


def test_top_rca_statement_is_generated(tmp_path):
    df = pd.DataFrame([
        _row("2026-01-01", "conversion_rate", actual=70, expected=100, region="APAC"),
    ])
    analyzer = RootCauseAnalyzer(config_path=str(CONFIG_PATH))
    table = analyzer.build_contribution_table(df)

    summary, top = analyzer.write_outputs(
        table,
        summary_path=tmp_path / "summary.json",
        top_causes_path=tmp_path / "top.csv",
        total_anomalies_analyzed=1,
    )

    assert summary["top_root_cause_statements"]
    assert summary["top_root_cause_by_kpi"]
    assert summary["top_root_cause_by_dimension"]
    assert "contributed" in summary["top_root_cause_statements"][0]
    assert not top.empty


def test_candidate_summary_explains_exclusions():
    df = pd.DataFrame([
        _row("2026-01-01", "conversion_rate", actual=80, expected=100, residual_anomaly=True),
        _row("2026-01-02", "conversion_rate", actual=120, expected=100, residual_anomaly=True),
        _row("2026-01-03", "conversion_rate", actual=80, expected=100, residual_anomaly=True),
    ])
    df.loc[2, "expected_value"] = pd.NA

    summary = RootCauseAnalyzer(config_path=str(CONFIG_PATH)).summarize_candidate_filter(df)

    assert summary["detector_anomaly_count"] == 3
    assert summary["valid_expected_baseline_count"] == 2
    assert summary["degrading_anomaly_count"] == 1
    assert summary["excluded_missing_expected_or_baseline"] == 1
    assert summary["excluded_non_degrading"] == 1


def test_pipeline_creates_rca_outputs():
    summary = run_phase_1_pipeline(regenerate=True)

    assert summary["rca_rows"] > 0
    assert Path(summary["rca_table_path"]).exists()
    assert Path(summary["root_cause_summary_path"]).exists()
    assert Path(summary["top_root_causes_path"]).exists()
