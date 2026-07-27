from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml


MONITORING_DIMENSIONS = [
    "kpi_name",
    "region",
    "device_type",
    "browser",
    "channel",
    "business_segment",
]

# Measure columns that follow the dimension columns in the output table. Held separately
# so the output schema can be rebuilt for any dimension set without duplicating this list.
MEASURE_COLUMNS = [
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

OUTPUT_COLUMNS = ["date", *MONITORING_DIMENSIONS, *MEASURE_COLUMNS]


class KPIMonitor:
    def __init__(
        self,
        config_path: str = "config/monitoring_config.yaml",
        dimensions: list[str] | None = None,
    ):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        self.thresholds = self._load_thresholds(self.config)
        # dimensions=None keeps the synthetic evaluation schema. The live operations track
        # passes its own dimension set (project/access/agent), which is why this is a
        # parameter rather than a module constant: the detector logic is schema-agnostic,
        # only the grouping key changes.
        self.dimensions = list(dimensions) if dimensions else list(MONITORING_DIMENSIONS)
        if not self.dimensions or self.dimensions[0] != "kpi_name":
            raise ValueError("dimensions must start with 'kpi_name'")
        self.output_columns = ["date", *self.dimensions, *MEASURE_COLUMNS]

    def build_monitoring_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Builds a same-grain KPI monitoring table from validated KPI observations."""
        required_columns = ["date", "kpi_name", "kpi_value", *self.dimensions[1:]]
        missing = [column for column in required_columns if column not in df.columns]
        if missing:
            raise ValueError(f"Cannot build KPI monitoring table. Missing columns: {missing}")

        monitoring = df.copy()
        monitoring["date"] = pd.to_datetime(monitoring["date"], errors="coerce")
        monitoring["actual_value"] = pd.to_numeric(monitoring["kpi_value"], errors="coerce")
        monitoring = monitoring.sort_values(["date", *self.dimensions]).reset_index(drop=True)

        grouped = monitoring.groupby(self.dimensions, sort=False)["actual_value"]
        monitoring["rolling_avg_7d"] = grouped.transform(
            lambda values: values.rolling(window=7, min_periods=1).mean()
        )
        monitoring["rolling_avg_14d"] = grouped.transform(
            lambda values: values.rolling(window=14, min_periods=1).mean()
        )
        monitoring["rolling_avg_28d"] = grouped.transform(
            lambda values: values.rolling(window=28, min_periods=1).mean()
        )
        monitoring["moving_baseline"] = grouped.transform(
            lambda values: values.shift(1).rolling(window=28, min_periods=7).mean()
        )
        monitoring["expected_value"] = monitoring["moving_baseline"]
        monitoring["absolute_variance"] = monitoring["actual_value"] - monitoring["expected_value"]
        monitoring["percent_variance"] = self._safe_percent_variance(
            monitoring["absolute_variance"],
            monitoring["expected_value"],
        )

        statuses = monitoring.apply(self._status_for_row, axis=1, result_type="expand")
        monitoring["threshold_value"] = statuses["threshold_value"]
        monitoring["threshold_direction"] = statuses["threshold_direction"]
        monitoring["threshold_breached"] = statuses["threshold_breached"].astype(bool)
        monitoring["monitoring_status"] = statuses["monitoring_status"]

        monitoring["date"] = monitoring["date"].dt.strftime("%Y-%m-%d")
        return monitoring[self.output_columns]

    def write_monitoring_summary(
        self,
        monitoring: pd.DataFrame,
        output_path: str | Path = "data/reports/kpi_monitoring_summary.json",
        monitoring_output_path: str | Path = "data/processed/kpi_monitoring_table.csv",
    ) -> dict:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        warning_count = int((monitoring["monitoring_status"] == "WARNING").sum())
        critical_count = int((monitoring["monitoring_status"] == "CRITICAL").sum())
        breached = monitoring[monitoring["threshold_breached"]]
        breach_count_by_kpi = {
            key: int(value)
            for key, value in breached.groupby("kpi_name").size().sort_index().items()
        }

        worst = (
            monitoring.dropna(subset=["percent_variance"])
            .assign(abs_percent_variance=lambda frame: frame["percent_variance"].abs())
            .sort_values("abs_percent_variance", ascending=False)
            .head(10)
        )
        worst_records = [
            {
                "date": row["date"],
                "kpi_name": row["kpi_name"],
                "region": row["region"],
                "device_type": row["device_type"],
                "browser": row["browser"],
                "channel": row["channel"],
                "business_segment": row["business_segment"],
                "actual_value": round(float(row["actual_value"]), 6),
                "expected_value": round(float(row["expected_value"]), 6),
                "percent_variance": round(float(row["percent_variance"]), 6),
                "monitoring_status": row["monitoring_status"],
            }
            for _, row in worst.iterrows()
        ]

        summary = {
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_monitoring_rows": int(len(monitoring)),
            "kpi_names": sorted(monitoring["kpi_name"].dropna().unique().tolist()),
            "date_range": {
                "min": monitoring["date"].min(),
                "max": monitoring["date"].max(),
            },
            "warning_count": warning_count,
            "critical_count": critical_count,
            "threshold_breach_count": int(monitoring["threshold_breached"].sum()),
            "threshold_breach_count_by_kpi": breach_count_by_kpi,
            "worst_kpi_variances_by_abs_percent_variance": worst_records,
            "outputs": {
                "monitoring_table": str(monitoring_output_path),
                "monitoring_summary": str(output_path),
            },
        }

        with open(output_path, "w") as f:
            json.dump(summary, f, indent=2)

        return summary

    def _status_for_row(self, row: pd.Series) -> dict:
        threshold = self.thresholds.get(row["kpi_name"], self._fallback_threshold())
        direction = threshold["direction"]
        warning = float(threshold["warning_threshold_pct"])
        critical = float(threshold["critical_threshold_pct"])
        percent_variance = row["percent_variance"]

        if pd.isna(percent_variance):
            return {
                "threshold_value": warning,
                "threshold_direction": direction,
                "threshold_breached": False,
                "monitoring_status": "NORMAL",
            }

        if direction == "higher_is_bad":
            if percent_variance >= critical:
                status = "CRITICAL"
            elif percent_variance >= warning:
                status = "WARNING"
            else:
                status = "NORMAL"
        else:
            if percent_variance <= -critical:
                status = "CRITICAL"
            elif percent_variance <= -warning:
                status = "WARNING"
            else:
                status = "NORMAL"

        return {
            "threshold_value": critical if status == "CRITICAL" else warning,
            "threshold_direction": direction,
            "threshold_breached": status != "NORMAL",
            "monitoring_status": status,
        }

    @staticmethod
    def _safe_percent_variance(absolute_variance: pd.Series, expected_value: pd.Series) -> pd.Series:
        percent = absolute_variance / expected_value
        percent = percent.mask(expected_value == 0)
        return percent.replace([float("inf"), float("-inf")], pd.NA)

    @staticmethod
    def _load_thresholds(config: dict) -> dict:
        thresholds = config.get("kpi_monitoring", {}).get("thresholds", {})
        return {
            kpi_name: {
                "warning_threshold_pct": float(values["warning_threshold_pct"]),
                "critical_threshold_pct": float(values["critical_threshold_pct"]),
                "direction": values["direction"],
            }
            for kpi_name, values in thresholds.items()
        }

    @staticmethod
    def _fallback_threshold() -> dict:
        return {
            "warning_threshold_pct": 0.05,
            "critical_threshold_pct": 0.10,
            "direction": "lower_is_bad",
        }
