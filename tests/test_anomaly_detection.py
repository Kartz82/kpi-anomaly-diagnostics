from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.run_pipeline import run_phase_1_pipeline
from src.core.anomaly_detection import ANOMALY_OUTPUT_COLUMNS, AnomalyDetector


CONFIG_PATH = ROOT_DIR / "config/monitoring_config.yaml"


def _monitoring_rows(values: list[float], kpi_name: str = "conversion_rate") -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=len(values), freq="D")
    baseline = pd.Series(values).shift(1).rolling(window=28, min_periods=7).mean()
    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "kpi_name": kpi_name,
        "region": "APAC",
        "device_type": "Mobile",
        "browser": "Safari",
        "channel": "Organic",
        "business_segment": "SMB",
        "actual_value": values,
        "rolling_avg_7d": pd.Series(values).rolling(7, min_periods=1).mean(),
        "rolling_avg_14d": pd.Series(values).rolling(14, min_periods=1).mean(),
        "rolling_avg_28d": pd.Series(values).rolling(28, min_periods=1).mean(),
        "moving_baseline": baseline,
        "expected_value": baseline,
        "absolute_variance": pd.Series(values) - baseline,
        "percent_variance": (pd.Series(values) - baseline) / baseline,
        "threshold_value": 0.08,
        "threshold_direction": "lower_is_bad",
        "threshold_breached": False,
        "monitoring_status": "NORMAL",
    })


def _validated_from_monitoring(monitoring: pd.DataFrame) -> pd.DataFrame:
    validated = monitoring[[
        "date",
        "kpi_name",
        "region",
        "device_type",
        "browser",
        "channel",
        "business_segment",
    ]].copy()
    validated["impressions"] = 1000
    validated["clicks"] = 100
    validated["conversions"] = 10
    validated["orders"] = 8
    validated["revenue"] = 800.0
    validated["latency_ms"] = 100.0
    validated["kpi_value"] = monitoring["actual_value"]
    validated["is_incident"] = False
    validated["incident_id"] = ""
    validated["incident_type"] = ""
    validated["incident_description"] = ""
    return validated


def test_anomaly_results_contain_required_columns():
    monitoring = _monitoring_rows([100, 101, 99, 100, 102, 98, 101, 150, 100, 99])
    validated = _validated_from_monitoring(monitoring)

    results = AnomalyDetector(config_path=str(CONFIG_PATH)).build_anomaly_results(monitoring, validated)

    assert list(results.columns) == ANOMALY_OUTPUT_COLUMNS


def test_zscore_handles_missing_baseline_and_does_not_flag_it():
    monitoring = _monitoring_rows([100, 101, 99, 100, 102, 98])
    detector = AnomalyDetector(config_path=str(CONFIG_PATH))

    results = detector._add_zscore_detector(monitoring.copy())

    assert results["z_score"].isna().all()
    assert results["zscore_anomaly"].sum() == 0
    assert set(results["zscore_severity"]) == {"NORMAL"}


def test_zscore_detector_flags_large_deviations():
    values = [100, 101, 99, 100, 102, 98, 101, 150]
    monitoring = _monitoring_rows(values)
    detector = AnomalyDetector(config_path=str(CONFIG_PATH))

    results = detector._add_zscore_detector(monitoring.copy())
    last = results.iloc[-1]

    assert bool(last["zscore_anomaly"]) is True
    assert last["zscore_severity"] == "CRITICAL"


def test_residual_detector_produces_prediction_and_residual_fields():
    values = [100 + (idx % 5) for idx in range(40)]
    values[-1] = 60
    monitoring = _monitoring_rows(values)
    detector = AnomalyDetector(config_path=str(CONFIG_PATH))

    results = detector._add_ml_residual_detector(monitoring.copy())

    assert results["predicted_value"].notna().all()
    assert results["residual"].notna().all()
    assert "residual_percent" in results.columns
    assert detector.residual_model_used in {
        "xgboost_xgbregressor",
        "sklearn_hist_gradient_boosting_regressor",
        "numpy_ridge_regression_residual",
    }


def test_residual_detector_does_not_use_incident_labels_as_features():
    monitoring = _monitoring_rows([100 + (idx % 5) for idx in range(20)])
    for column in ["is_incident", "incident_id", "incident_type", "incident_description"]:
        monitoring[column] = "SHOULD_NOT_BE_USED"

    features = AnomalyDetector(config_path=str(CONFIG_PATH))._build_model_features(monitoring)

    assert "is_incident" not in features.columns
    assert not any(column.startswith("incident_") for column in features.columns)


def test_combined_anomaly_and_severity_prioritization():
    detector = AnomalyDetector(config_path=str(CONFIG_PATH))
    df = pd.DataFrame({
        "zscore_anomaly": [False, True, True],
        "zscore_severity": ["NORMAL", "WARNING", "CRITICAL"],
        "residual_anomaly": [True, False, True],
        "residual_severity": ["WARNING", "NORMAL", "WARNING"],
    })

    results = detector._add_combined_detector(df)

    assert results["combined_anomaly"].tolist() == [True, True, True]
    assert results["combined_severity"].tolist() == ["WARNING", "WARNING", "CRITICAL"]


def test_full_pipeline_runs_with_phase_3_outputs():
    summary = run_phase_1_pipeline(regenerate=True)

    assert summary["anomaly_rows"] == summary["monitoring_rows"]
    assert summary["combined_anomaly_count"] >= 0
    assert Path(summary["anomaly_results_path"]).exists()
