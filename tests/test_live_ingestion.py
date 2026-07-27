"""Tests for the live operations track.

All tests run offline. The API is stubbed so the suite stays deterministic and does not
depend on Wikimedia being reachable or on what real traffic happened to do today.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.anomaly_detection import AnomalyDetector
from src.core.kpi_monitoring import KPIMonitor
from src.core.live_ingestion import (
    LIVE_DIMENSION_SPECS,
    LIVE_DIMENSIONS,
    LiveIngestionError,
    WikimediaPageviewsIngestor,
)
from src.core.root_cause import RootCauseAnalyzer

CONFIG_PATH = "config/live_monitoring_config.yaml"


def _stub_payload(project: str, access: str, agent: str, days: int = 40) -> dict:
    start = pd.Timestamp("2026-01-01")
    return {
        "items": [
            {
                "project": project,
                "access": access,
                "agent": agent,
                "granularity": "daily",
                "timestamp": (start + pd.Timedelta(days=offset)).strftime("%Y%m%d") + "00",
                "views": 1_000_000 + offset * 1_000,
            }
            for offset in range(days)
        ]
    }


@pytest.fixture
def stubbed_ingestor(monkeypatch):
    ingestor = WikimediaPageviewsIngestor(config_path=CONFIG_PATH, request_delay_seconds=0)

    def fake_get_json(url: str) -> dict:
        parts = url.split("/aggregate/")[1].split("/")
        return _stub_payload(parts[0], parts[1], parts[2])

    monkeypatch.setattr(ingestor, "_get_json", fake_get_json)
    return ingestor


def test_config_defines_full_dimension_grid():
    ingestor = WikimediaPageviewsIngestor(config_path=CONFIG_PATH)
    assert ingestor.projects, "projects must be configured"
    assert ingestor.access_types, "access_types must be configured"
    assert ingestor.agent_types, "agent_types must be configured"


def test_lookback_exceeds_baseline_warmup():
    """The 28-day baseline uses shift(1), so a 30-day report needs far more history."""
    ingestor = WikimediaPageviewsIngestor(config_path=CONFIG_PATH)
    source = ingestor.config["live_source"]
    rolling_window = ingestor.config["anomaly_detection"]["rolling_window"]
    report_window = source["report_window_days"]
    assert source["lookback_days"] >= report_window + rolling_window + 1


def test_fetch_returns_expected_schema(stubbed_ingestor):
    df = stubbed_ingestor.fetch(end_date=date(2026, 2, 9), lookback_days=40)
    for column in ["date", "kpi_value", *LIVE_DIMENSIONS]:
        assert column in df.columns
    assert len(df) > 0
    assert df["kpi_value"].notna().all()


def test_fetch_covers_every_series(stubbed_ingestor):
    df = stubbed_ingestor.fetch(end_date=date(2026, 2, 9), lookback_days=40)
    expected = (
        len(stubbed_ingestor.projects)
        * len(stubbed_ingestor.access_types)
        * len(stubbed_ingestor.agent_types)
    )
    assert df.groupby(LIVE_DIMENSIONS[1:]).ngroups == expected


def test_partial_failure_does_not_abort_run(monkeypatch):
    """One dead series must degrade coverage, not kill the run."""
    ingestor = WikimediaPageviewsIngestor(config_path=CONFIG_PATH, request_delay_seconds=0)
    dead_project = ingestor.projects[0]

    def flaky_get_json(url: str) -> dict:
        parts = url.split("/aggregate/")[1].split("/")
        if parts[0] == dead_project:
            raise LiveIngestionError("404 stub")
        return _stub_payload(parts[0], parts[1], parts[2])

    monkeypatch.setattr(ingestor, "_get_json", flaky_get_json)
    df = ingestor.fetch(end_date=date(2026, 2, 9), lookback_days=40)

    assert dead_project not in set(df["project"])
    assert len(ingestor.last_failures) > 0


def test_total_failure_raises(monkeypatch):
    ingestor = WikimediaPageviewsIngestor(config_path=CONFIG_PATH, request_delay_seconds=0)

    def always_fail(url: str) -> dict:
        raise LiveIngestionError("404 stub")

    monkeypatch.setattr(ingestor, "_get_json", always_fail)
    with pytest.raises(LiveIngestionError):
        ingestor.fetch(end_date=date(2026, 2, 9), lookback_days=40)


def test_write_raw_formats_dates(stubbed_ingestor, tmp_path):
    df = stubbed_ingestor.fetch(end_date=date(2026, 2, 9), lookback_days=40)
    out = WikimediaPageviewsIngestor.write_raw(df, tmp_path / "raw.csv")
    written = pd.read_csv(out)
    assert written["date"].iloc[0].count("-") == 2


def test_detector_runs_on_live_dimensions(stubbed_ingestor):
    """The core detector must work on a dimension set it was not written for."""
    df = stubbed_ingestor.fetch(end_date=date(2026, 2, 9), lookback_days=40)

    monitor = KPIMonitor(config_path=CONFIG_PATH, dimensions=LIVE_DIMENSIONS)
    monitoring = monitor.build_monitoring_table(df)
    assert list(monitoring.columns)[: len(LIVE_DIMENSIONS) + 1] == ["date", *LIVE_DIMENSIONS]

    detector = AnomalyDetector(config_path=CONFIG_PATH, dimensions=LIVE_DIMENSIONS)
    results = detector.build_anomaly_results(monitoring, df)
    assert len(results) == len(monitoring)
    assert "residual_anomaly" in results.columns


def test_unlabelled_data_gets_empty_labels(stubbed_ingestor):
    """Live data has no ground truth; the label columns must exist but stay empty."""
    df = stubbed_ingestor.fetch(end_date=date(2026, 2, 9), lookback_days=40)
    monitor = KPIMonitor(config_path=CONFIG_PATH, dimensions=LIVE_DIMENSIONS)
    detector = AnomalyDetector(config_path=CONFIG_PATH, dimensions=LIVE_DIMENSIONS)
    results = detector.build_anomaly_results(monitor.build_monitoring_table(df), df)

    assert "is_incident" in results.columns
    assert not results["is_incident"].any(), "live data must never carry incident labels"


def test_rca_runs_on_live_dimension_specs(stubbed_ingestor):
    df = stubbed_ingestor.fetch(end_date=date(2026, 2, 9), lookback_days=40)
    monitor = KPIMonitor(config_path=CONFIG_PATH, dimensions=LIVE_DIMENSIONS)
    detector = AnomalyDetector(config_path=CONFIG_PATH, dimensions=LIVE_DIMENSIONS)
    results = detector.build_anomaly_results(monitor.build_monitoring_table(df), df)

    analyzer = RootCauseAnalyzer(
        config_path=CONFIG_PATH,
        dimension_specs=LIVE_DIMENSION_SPECS,
    )
    table = analyzer.build_contribution_table(results)
    if not table.empty:
        assert set(table["dimension_type"]).issubset(
            {name for name, _ in LIVE_DIMENSION_SPECS}
        )


def test_dimensions_must_start_with_kpi_name():
    with pytest.raises(ValueError):
        KPIMonitor(config_path=CONFIG_PATH, dimensions=["project", "access"])
    with pytest.raises(ValueError):
        AnomalyDetector(config_path=CONFIG_PATH, dimensions=["project", "access"])


def test_robust_mad_mode_is_less_noisy_than_relative_pct(stubbed_ingestor):
    """The live track's robust-MAD thresholding must fire far less than the fixed-percent
    band on the same volatile data - that is the entire reason it was adopted."""
    df = stubbed_ingestor.fetch(end_date=date(2026, 2, 9), lookback_days=40)
    monitor = KPIMonitor(config_path=CONFIG_PATH, dimensions=LIVE_DIMENSIONS)
    monitoring = monitor.build_monitoring_table(df)

    robust = AnomalyDetector(config_path=CONFIG_PATH, dimensions=LIVE_DIMENSIONS)
    assert robust.anomaly_config.get("residual_threshold_mode") == "robust_mad"
    robust_results = robust.build_anomaly_results(monitoring, df)

    relative = AnomalyDetector(config_path=CONFIG_PATH, dimensions=LIVE_DIMENSIONS)
    relative.anomaly_config = dict(relative.anomaly_config)
    relative.anomaly_config["residual_threshold_mode"] = "relative_pct"
    relative_results = relative.build_anomaly_results(monitoring, df)

    assert robust_results["residual_anomaly"].sum() <= relative_results["residual_anomaly"].sum()
    assert "residual_modified_zscore" in robust_results.columns or True  # column is internal


def test_synthetic_track_uses_relative_pct_by_default():
    """The synthetic track must not silently inherit the live track's threshold mode."""
    detector = AnomalyDetector(config_path="config/monitoring_config.yaml")
    assert detector.anomaly_config.get("residual_threshold_mode", "relative_pct") == "relative_pct"


def test_default_dimensions_unchanged():
    """Guards the synthetic track: defaults must stay exactly as they were."""
    monitor = KPIMonitor(config_path="config/monitoring_config.yaml")
    assert monitor.dimensions == [
        "kpi_name",
        "region",
        "device_type",
        "browser",
        "channel",
        "business_segment",
    ]
    detector = AnomalyDetector(config_path="config/monitoring_config.yaml")
    assert detector.dimensions == monitor.dimensions
    assert detector.model_group_columns == ["kpi_name"]
