from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml


BUSINESS_KEY = [
    "date",
    "kpi_name",
    "region",
    "device_type",
    "browser",
    "channel",
    "business_segment",
]

RCA_OUTPUT_COLUMNS = [
    "analysis_date",
    "kpi_name",
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


class RootCauseAnalyzer:
    # Dimension hierarchy analysed for contribution: each entry is
    # (dimension_type label, columns to group by). Single-column entries isolate one
    # dimension; multi-column entries find interaction effects (e.g. a fault that only
    # appears for one region+device+browser combination).
    DEFAULT_DIMENSION_SPECS = [
        ("region", ["region"]),
        ("device_type", ["device_type"]),
        ("browser", ["browser"]),
        ("channel", ["channel"]),
        ("business_segment", ["business_segment"]),
        ("region_device_browser", ["region", "device_type", "browser"]),
        (
            "full_segment",
            ["region", "device_type", "browser", "channel", "business_segment"],
        ),
    ]

    def __init__(
        self,
        segments: list | None = None,
        config_path: str = "config/monitoring_config.yaml",
        dimension_specs: list | None = None,
    ):
        self.segments = segments or []
        self.config_path = config_path
        # Injectable so the live operations track can analyse its own dimensions
        # (project/access/agent) with the same contribution maths.
        self.dimension_specs = [
            (name, list(columns))
            for name, columns in (dimension_specs or self.DEFAULT_DIMENSION_SPECS)
        ]
        self.config = self._load_config(config_path)
        self.rca_config = self.config.get("root_cause_analysis", {})
        self.kpi_directions = {
            kpi: values.get("direction", "lower_is_bad")
            for kpi, values in self.config.get("kpi_monitoring", {}).get("thresholds", {}).items()
        }

    def build_contribution_table(
        self,
        anomaly_results: pd.DataFrame,
        detector: str | None = None,
    ) -> pd.DataFrame:
        detector = detector or self.rca_config.get("default_detector", "residual_anomaly")
        self._validate_detector(detector)

        candidates = self._filter_rca_candidates(anomaly_results, detector)
        if candidates.empty:
            return pd.DataFrame(columns=RCA_OUTPUT_COLUMNS)

        candidates = candidates.copy()
        candidates["analysis_date"] = candidates["date"]
        candidates["degradation_amount"] = candidates.apply(self._degradation_amount, axis=1)
        candidates = candidates[candidates["degradation_amount"] > 0].copy()
        if candidates.empty:
            return pd.DataFrame(columns=RCA_OUTPUT_COLUMNS)

        rows = []
        dimensions = self.dimension_specs

        for (analysis_date, kpi_name), group in candidates.groupby(["analysis_date", "kpi_name"]):
            total_degradation = float(group["degradation_amount"].sum())
            if total_degradation <= 0:
                continue

            for dimension_type, columns in dimensions:
                grouped = group.groupby(columns, dropna=False)
                for dimension_values, dimension_group in grouped:
                    if not isinstance(dimension_values, tuple):
                        dimension_values = (dimension_values,)

                    degradation = float(dimension_group["degradation_amount"].sum())
                    rows.append({
                        "analysis_date": analysis_date,
                        "kpi_name": kpi_name,
                        "detector_used": detector,
                        "dimension_type": dimension_type,
                        "dimension_value": " + ".join(str(value) for value in dimension_values),
                        "actual_value_sum_or_avg": float(dimension_group["actual_value"].mean()),
                        "expected_value_sum_or_avg": float(dimension_group["expected_value"].mean()),
                        "degradation_amount": degradation,
                        "contribution_share": degradation / total_degradation,
                        "anomaly_count": int(len(dimension_group)),
                        "severity_max": self._max_severity(dimension_group, detector),
                        "recommended_action": self._recommended_action(
                            kpi_name,
                            dimension_type,
                            " + ".join(str(value) for value in dimension_values),
                        ),
                    })

        contribution_table = pd.DataFrame(rows)
        if contribution_table.empty:
            return pd.DataFrame(columns=RCA_OUTPUT_COLUMNS)

        contribution_table["contribution_rank"] = (
            contribution_table
            .sort_values(["contribution_share", "degradation_amount"], ascending=False)
            .groupby(["analysis_date", "kpi_name", "dimension_type"])
            .cumcount()
            + 1
        )
        contribution_table = contribution_table.sort_values(
            ["analysis_date", "kpi_name", "dimension_type", "contribution_rank"]
        )
        return contribution_table[RCA_OUTPUT_COLUMNS]

    def write_outputs(
        self,
        contribution_table: pd.DataFrame,
        summary_path: str | Path = "data/reports/root_cause_summary.json",
        top_causes_path: str | Path = "data/reports/top_root_causes.csv",
        detector: str | None = None,
        total_anomalies_analyzed: int | None = None,
        candidate_summary: dict | None = None,
    ) -> tuple[dict, pd.DataFrame]:
        detector = detector or self.rca_config.get("default_detector", "residual_anomaly")
        summary_path = Path(summary_path)
        top_causes_path = Path(top_causes_path)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        top_causes_path.parent.mkdir(parents=True, exist_ok=True)

        max_top = int(self.rca_config.get("max_top_contributors", 10))
        min_share = float(self.rca_config.get("minimum_contribution_share", 0.05))
        overall_top_causes = (
            contribution_table[
                (contribution_table["dimension_type"].isin(["region_device_browser", "full_segment"]))
                & (contribution_table["contribution_share"] >= min_share)
            ]
            .sort_values(["contribution_share", "degradation_amount"], ascending=False)
            .head(max_top)
            .copy()
        )
        top_by_kpi = self._top_root_cause_by_kpi(contribution_table)
        top_by_dimension = self._top_root_cause_by_dimension(contribution_table)
        top_causes = (
            pd.concat([top_by_kpi, top_by_dimension, overall_top_causes], ignore_index=True)
            .drop_duplicates(
                subset=["analysis_date", "kpi_name", "dimension_type", "dimension_value"],
                keep="first",
            )
            .head(max_top)
            .copy()
        )
        top_causes["root_cause_statement"] = top_causes.apply(self._statement_for_row, axis=1)
        top_causes.to_csv(top_causes_path, index=False)
        overall_top_causes["root_cause_statement"] = overall_top_causes.apply(self._statement_for_row, axis=1)
        top_by_kpi["root_cause_statement"] = top_by_kpi.apply(self._statement_for_row, axis=1)
        top_by_dimension["root_cause_statement"] = top_by_dimension.apply(self._statement_for_row, axis=1)

        summary = {
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "detector_used": detector,
            "total_anomalies_analyzed": int(total_anomalies_analyzed or 0),
            "candidate_summary": candidate_summary or {},
            "kpi_names_analyzed": sorted(contribution_table["kpi_name"].dropna().unique().tolist()),
            "top_root_cause_statements": top_causes["root_cause_statement"].head(max_top).tolist(),
            "top_overall_root_causes": overall_top_causes.head(max_top).to_dict(orient="records"),
            "top_root_cause_by_kpi": top_by_kpi.to_dict(orient="records"),
            "top_root_cause_by_dimension": top_by_dimension.to_dict(orient="records"),
            "top_contributors_by_kpi": self._top_contributors_by_kpi(contribution_table, max_top),
            "top_contributors_by_dimension": self._top_contributors_by_dimension(contribution_table, max_top),
            "recommended_action_examples": top_causes["recommended_action"].drop_duplicates().head(5).tolist(),
            "method_notes": [
                "RCA uses residual_anomaly by default because Phase 3 model evaluation selected ml_residual as best by F1.",
                "Contribution share is calculated within each KPI/date from positive degradation only.",
                "Rate KPI rows are averaged for display, while degradation_amount is summed for contribution share.",
                "Residual anomalies without prior baseline/expected values are excluded from contribution math.",
                "Incident labels are not used in RCA logic.",
            ],
            "limitations": [
                "RCA is contribution-based, not causal proof.",
                "Synthetic data makes the diagnostic patterns easier than real production data.",
            ],
            "outputs": {
                "root_cause_summary": str(summary_path),
                "top_root_causes": str(top_causes_path),
            },
        }
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        return summary, top_causes

    def count_rca_candidates(self, anomaly_results: pd.DataFrame, detector: str | None = None) -> int:
        detector = detector or self.rca_config.get("default_detector", "residual_anomaly")
        return int(len(self._filter_rca_candidates(anomaly_results, detector)))

    def summarize_candidate_filter(self, anomaly_results: pd.DataFrame, detector: str | None = None) -> dict:
        detector = detector or self.rca_config.get("default_detector", "residual_anomaly")
        detector_anomalies = anomaly_results[anomaly_results[detector].astype(bool)].copy()
        valid = detector_anomalies[
            detector_anomalies["expected_value"].notna()
            & detector_anomalies["moving_baseline"].notna()
            & detector_anomalies["percent_variance"].notna()
        ].copy()
        if valid.empty:
            degrading = valid
        else:
            valid["degradation_amount"] = valid.apply(self._degradation_amount, axis=1)
            degrading = valid[valid["degradation_amount"] > 0]

        return {
            "detector_anomaly_count": int(len(detector_anomalies)),
            "valid_expected_baseline_count": int(len(valid)),
            "degrading_anomaly_count": int(len(degrading)),
            "excluded_missing_expected_or_baseline": int(len(detector_anomalies) - len(valid)),
            "excluded_non_degrading": int(len(valid) - len(degrading)),
        }

    def _filter_rca_candidates(self, anomaly_results: pd.DataFrame, detector: str) -> pd.DataFrame:
        severity_column = self._severity_column_for_detector(detector)
        required = [detector, "expected_value", "moving_baseline", "percent_variance", severity_column]
        missing = [column for column in required if column not in anomaly_results.columns]
        if missing:
            raise ValueError(f"Cannot run RCA. Missing columns: {missing}")

        candidates = anomaly_results[
            (anomaly_results[detector].astype(bool))
            & (anomaly_results[severity_column].isin(["WARNING", "CRITICAL"]))
            & (anomaly_results["expected_value"].notna())
            & (anomaly_results["moving_baseline"].notna())
            & (anomaly_results["percent_variance"].notna())
        ].copy()
        return candidates

    def _degradation_amount(self, row: pd.Series) -> float:
        direction = self.kpi_directions.get(row["kpi_name"], "lower_is_bad")
        actual = float(row["actual_value"])
        expected = float(row["expected_value"])
        if direction == "higher_is_bad":
            return max(actual - expected, 0.0)
        return max(expected - actual, 0.0)

    def _max_severity(self, group: pd.DataFrame, detector: str) -> str:
        severity_column = self._severity_column_for_detector(detector)
        severity_rank = {"NORMAL": 0, "WARNING": 1, "CRITICAL": 2}
        max_rank = group[severity_column].map(severity_rank).fillna(0).max()
        return {value: key for key, value in severity_rank.items()}[int(max_rank)]

    @staticmethod
    def _severity_column_for_detector(detector: str) -> str:
        if detector == "residual_anomaly":
            return "residual_severity"
        if detector == "zscore_anomaly":
            return "zscore_severity"
        if detector == "combined_anomaly":
            return "combined_severity"
        if detector == "threshold_breached":
            return "monitoring_status"
        raise ValueError(f"Unsupported detector for RCA: {detector}")

    def _validate_detector(self, detector: str) -> None:
        allowed = self.rca_config.get(
            "allowed_detectors",
            ["residual_anomaly", "zscore_anomaly", "combined_anomaly", "threshold_breached"],
        )
        if detector not in allowed:
            raise ValueError(f"Detector {detector} is not allowed. Allowed detectors: {allowed}")

    def _statement_for_row(self, row: pd.Series) -> str:
        direction = self.kpi_directions.get(row["kpi_name"], "lower_is_bad")
        action = "accounted for" if direction == "higher_is_bad" else "contributed"
        suffix = "excess latency" if direction == "higher_is_bad" else "measured degradation"
        return (
            f"For {row['kpi_name']} on {row['analysis_date']}, "
            f"{row['dimension_value']} {action} "
            f"{row['contribution_share'] * 100:.1f}% of {suffix}."
        )

    @staticmethod
    def _recommended_action(kpi_name: str, dimension_type: str, dimension_value: str) -> str:
        return (
            f"Review {kpi_name} drivers for {dimension_type} = {dimension_value}; "
            "check recent releases, tracking changes, campaign mix, and operational issues."
        )

    @staticmethod
    def _top_contributors_by_kpi(contribution_table: pd.DataFrame, max_top: int) -> dict:
        result = {}
        for kpi_name, group in contribution_table.groupby("kpi_name"):
            result[kpi_name] = (
                group.sort_values(["contribution_share", "degradation_amount"], ascending=False)
                .head(max_top)
                .to_dict(orient="records")
            )
        return result

    @staticmethod
    def _top_contributors_by_dimension(contribution_table: pd.DataFrame, max_top: int) -> dict:
        result = {}
        for dimension_type, group in contribution_table.groupby("dimension_type"):
            result[dimension_type] = (
                group.sort_values(["contribution_share", "degradation_amount"], ascending=False)
                .head(max_top)
                .to_dict(orient="records")
            )
        return result

    @staticmethod
    def _top_root_cause_by_kpi(contribution_table: pd.DataFrame) -> pd.DataFrame:
        preferred = contribution_table[
            contribution_table["dimension_type"].isin(["region_device_browser", "full_segment"])
        ]
        if preferred.empty:
            preferred = contribution_table
        return (
            preferred.sort_values(["degradation_amount", "contribution_share"], ascending=False)
            .groupby("kpi_name", as_index=False)
            .head(1)
            .reset_index(drop=True)
        )

    @staticmethod
    def _top_root_cause_by_dimension(contribution_table: pd.DataFrame) -> pd.DataFrame:
        return (
            contribution_table.sort_values(["degradation_amount", "contribution_share"], ascending=False)
            .groupby("dimension_type", as_index=False)
            .head(1)
            .reset_index(drop=True)
        )

    @staticmethod
    def _load_config(config_path: str) -> dict:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def analyze_failure(self, df: pd.DataFrame, metric: str) -> dict:
        """Legacy row-ranking method retained for the original demo path."""
        anomaly_col = f'{metric}_anomaly'
        zscore_col = f'{metric}_zscore'
        anomalies = df[df[anomaly_col] == True].copy()

        if anomalies.empty:
            return {
                "anomaly_detected": False,
                "metric": metric,
                "date": None,
                "primary_offender": None,
                "ranked_anomalies": [],
                "summary": "No significant anomalies detected."
            }

        anomalies["severity"] = anomalies[zscore_col].abs()
        ranked = anomalies.sort_values("severity", ascending=False)
        worst_case = ranked.iloc[0]

        ranked_anomalies = []
        for _, row in ranked.head(10).iterrows():
            ranked_anomalies.append({
                "date": row["date"],
                "segment": {s: row[s] for s in self.segments},
                "z_score": round(float(row[zscore_col]), 2),
                "actual_value": round(float(row[metric]), 4),
                "rolling_mean": round(float(row["rolling_mean"]), 4)
            })

        return {
            "anomaly_detected": True,
            "metric": metric,
            "date": worst_case['date'],
            "primary_offender": {
                "segment": {s: worst_case[s] for s in self.segments},
                "z_score": round(float(worst_case[zscore_col]), 2),
                "actual_value": round(float(worst_case[metric]), 4),
                "rolling_mean": round(float(worst_case["rolling_mean"]), 4)
            },
            "ranked_anomalies": ranked_anomalies,
            "summary": "Anomaly detected and ranked by absolute Z-score severity."
        }
