from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.generate_raw_data import generate_kpi_data
from src.core.data_quality import DataQualityValidator


SCHEMA_CONTRACT_PATH = ROOT_DIR / "config/schema_contract.yaml"


@pytest.fixture(scope="module")
def valid_dataset(tmp_path_factory):
    # Anchored to today, not to the generator's pinned default end date.
    #
    # The quality suite includes a freshness check (max 14 days since the latest date).
    # Generating with the pinned default makes this test pass only for the two weeks
    # after that date and fail forever afterwards - which is exactly what happened: the
    # shipped dataset ends 2026-06-30, so this test started failing around 2026-07-14.
    #
    # A freshness check has to be exercised with fresh data. Incident windows are offsets
    # from the end date, so the labelled ground truth moves with the anchor.
    output_path = tmp_path_factory.mktemp("raw") / "kpi_daily_metrics.csv"
    return generate_kpi_data(output_path=output_path, end_date=date.today().isoformat())


@pytest.fixture
def validator():
    return DataQualityValidator(str(SCHEMA_CONTRACT_PATH))


def test_valid_generated_dataset_passes_quality_validation(valid_dataset, validator):
    report = validator.run_checks(valid_dataset)

    assert report["status"] == "PASS"
    assert report["is_healthy"] is True
    assert report["health_score"] == 100
    assert report["checks"]["schema"]["passed"] is True
    assert report["checks"]["duplicates"]["duplicate_count"] == 0


def test_schema_validation_catches_missing_required_columns(valid_dataset, validator):
    broken = valid_dataset.drop(columns=["kpi_name"])

    report = validator.run_checks(broken)

    assert report["status"] == "FAIL"
    assert report["checks"]["schema"]["passed"] is False
    assert "kpi_name" in report["checks"]["schema"]["missing_columns"]


def test_null_detection_catches_required_field_nulls(valid_dataset, validator):
    broken = valid_dataset.copy()
    broken.loc[0, "region"] = pd.NA

    report = validator.run_checks(broken)

    assert report["status"] == "FAIL"
    assert report["checks"]["nulls"]["passed"] is False
    assert report["checks"]["nulls"]["null_counts"]["region"] == 1


def test_duplicate_detection_catches_duplicate_business_keys(valid_dataset, validator):
    broken = pd.concat([valid_dataset, valid_dataset.head(1)], ignore_index=True)

    report = validator.run_checks(broken)

    assert report["status"] == "FAIL"
    assert report["checks"]["duplicates"]["passed"] is False
    assert report["checks"]["duplicates"]["duplicate_count"] == 2


def test_accepted_values_validation_catches_invalid_dimensions(valid_dataset, validator):
    broken = valid_dataset.copy()
    broken.loc[0, "region"] = "Mars"

    report = validator.run_checks(broken)

    assert report["status"] == "FAIL"
    assert report["checks"]["accepted_values"]["passed"] is False
    assert "Mars" in report["checks"]["accepted_values"]["failures"]["region"]


def test_freshness_check_fails_for_stale_data(valid_dataset, validator):
    broken = valid_dataset.copy()
    broken["date"] = "2025-01-01"

    report = validator.run_checks(broken)

    assert report["status"] == "FAIL"
    assert report["checks"]["freshness"]["passed"] is False


def test_completeness_check_fails_when_dates_are_missing(valid_dataset, validator):
    broken = valid_dataset[~valid_dataset["date"].isin([
        "2026-04-10",
        "2026-04-11",
        "2026-04-12",
        "2026-04-13",
        "2026-04-14",
        "2026-04-15",
        "2026-04-16",
        "2026-04-17",
        "2026-04-18",
        "2026-04-19",
    ])].copy()

    report = validator.run_checks(broken)

    assert report["status"] == "FAIL"
    assert report["checks"]["completeness"]["passed"] is False


def test_health_score_decreases_when_issues_are_introduced(valid_dataset, validator):
    clean_report = validator.run_checks(valid_dataset)

    broken = valid_dataset.copy()
    broken.loc[0, "region"] = pd.NA
    broken.loc[1, "latency_ms"] = 5000
    broken = pd.concat([broken, broken.head(1)], ignore_index=True)
    broken["date"] = "2025-01-01"

    broken_report = validator.run_checks(broken)

    assert broken_report["health_score"] < clean_report["health_score"]
    assert broken_report["status"] == "FAIL"
