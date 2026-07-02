from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


class ModelEvaluator:
    DETECTOR_COLUMNS = {
        "monitoring_threshold": "threshold_breached",
        "rolling_zscore": "zscore_anomaly",
        "ml_residual": "residual_anomaly",
        "combined": "combined_anomaly",
    }

    def evaluate(self, anomaly_results: pd.DataFrame) -> pd.DataFrame:
        y_true = anomaly_results["is_incident"].astype(bool)
        rows = []
        for detector, column in self.DETECTOR_COLUMNS.items():
            y_pred = anomaly_results[column].astype(bool)
            rows.append(self._metrics_for_detector(detector, y_true, y_pred))
        return pd.DataFrame(rows)

    def write_outputs(
        self,
        anomaly_results: pd.DataFrame,
        evaluation_path: str | Path = "data/reports/model_evaluation.csv",
        comparison_path: str | Path = "data/reports/model_comparison.json",
        residual_model_used: str = "unknown",
        method_metadata: dict | None = None,
    ) -> tuple[pd.DataFrame, dict]:
        evaluation_path = Path(evaluation_path)
        comparison_path = Path(comparison_path)
        evaluation_path.parent.mkdir(parents=True, exist_ok=True)
        comparison_path.parent.mkdir(parents=True, exist_ok=True)

        evaluation = self.evaluate(anomaly_results)
        evaluation.to_csv(evaluation_path, index=False)

        best_row = evaluation.sort_values(
            ["f1_score", "recall", "precision"],
            ascending=False,
        ).iloc[0]
        comparison = {
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "best_detector": best_row["detector"],
            "best_detector_metric": "f1_score",
            "best_detector_f1_score": float(best_row["f1_score"]),
            "residual_model_used": residual_model_used,
            "method_metadata": method_metadata or {
                "residual_model_used": residual_model_used,
                "xgboost_used": residual_model_used == "xgboost_xgbregressor",
                "fallback_note": (
                    "The comparison reports the actual residual method used in "
                    "this run. Synthetic labels are excluded from detector features."
                ),
            },
            "ground_truth_label": "is_incident",
            "label_note": (
                "Synthetic incident labels are used only for evaluation, not as "
                "features in anomaly detectors."
            ),
            "evaluation_rows": evaluation.to_dict(orient="records"),
            "outputs": {
                "model_evaluation": str(evaluation_path),
                "model_comparison": str(comparison_path),
            },
        }
        with open(comparison_path, "w") as f:
            json.dump(comparison, f, indent=2)

        return evaluation, comparison

    @staticmethod
    def _metrics_for_detector(detector: str, y_true: pd.Series, y_pred: pd.Series) -> dict:
        tp = int((y_true & y_pred).sum())
        fp = int((~y_true & y_pred).sum())
        fn = int((y_true & ~y_pred).sum())
        tn = int((~y_true & ~y_pred).sum())

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

        return {
            "detector": detector,
            "precision": round(float(precision), 6),
            "recall": round(float(recall), 6),
            "f1_score": round(float(f1), 6),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn,
            "support": int(y_true.sum()),
            "total_rows": int(len(y_true)),
        }
