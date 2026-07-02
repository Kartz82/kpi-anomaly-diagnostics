from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.model_evaluation import ModelEvaluator


def test_evaluation_metrics_calculate_correctly_on_controlled_example():
    df = pd.DataFrame({
        "is_incident": [True, True, False, False],
        "threshold_breached": [True, False, True, False],
        "zscore_anomaly": [True, True, False, False],
        "residual_anomaly": [False, False, False, False],
        "combined_anomaly": [True, True, False, False],
    })

    evaluation = ModelEvaluator().evaluate(df)
    monitoring = evaluation[evaluation["detector"] == "monitoring_threshold"].iloc[0]
    zscore = evaluation[evaluation["detector"] == "rolling_zscore"].iloc[0]
    residual = evaluation[evaluation["detector"] == "ml_residual"].iloc[0]

    assert monitoring["true_positives"] == 1
    assert monitoring["false_positives"] == 1
    assert monitoring["false_negatives"] == 1
    assert monitoring["true_negatives"] == 1
    assert monitoring["precision"] == 0.5
    assert monitoring["recall"] == 0.5
    assert monitoring["f1_score"] == 0.5

    assert zscore["precision"] == 1.0
    assert zscore["recall"] == 1.0
    assert zscore["f1_score"] == 1.0

    assert residual["precision"] == 0.0
    assert residual["recall"] == 0.0
    assert residual["false_negatives"] == 2


def test_false_positives_and_false_negatives_are_counted_correctly():
    df = pd.DataFrame({
        "is_incident": [True, True, True, False, False],
        "threshold_breached": [True, False, False, True, False],
        "zscore_anomaly": [False, False, False, False, False],
        "residual_anomaly": [True, True, False, False, True],
        "combined_anomaly": [True, True, False, False, True],
    })

    evaluation = ModelEvaluator().evaluate(df)
    residual = evaluation[evaluation["detector"] == "ml_residual"].iloc[0]

    assert residual["true_positives"] == 2
    assert residual["false_positives"] == 1
    assert residual["false_negatives"] == 1
    assert residual["true_negatives"] == 1
