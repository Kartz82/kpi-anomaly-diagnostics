from __future__ import annotations

import numpy as np
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

LABEL_COLUMNS = [
    "is_incident",
    "incident_id",
    "incident_type",
    "incident_description",
]

ANOMALY_OUTPUT_COLUMNS = [
    *BUSINESS_KEY,
    "actual_value",
    "expected_value",
    "moving_baseline",
    "percent_variance",
    "monitoring_status",
    "threshold_breached",
    "z_score",
    "zscore_anomaly",
    "zscore_severity",
    "predicted_value",
    "residual",
    "residual_percent",
    "residual_anomaly",
    "residual_severity",
    "combined_anomaly",
    "combined_severity",
    *LABEL_COLUMNS,
]


class AnomalyDetector:
    def __init__(
        self,
        threshold: float = 2.0,
        window: int = 7,
        config_path: str = "config/monitoring_config.yaml",
    ):
        self.z_threshold = threshold
        self.window = window
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.anomaly_config = self.config.get("anomaly_detection", {})
        self.residual_model_used = "unknown"
        self.residual_train_split_date = None

    def detect_anomalies(self, df: pd.DataFrame, metric: str) -> pd.DataFrame:
        """Legacy detector retained for the original demo path."""
        df = df.sort_values('date').copy()

        group_cols = ['device_type', 'region', 'browser']
        grouped_metric = df.groupby(group_cols)[metric]

        df['rolling_mean'] = grouped_metric.transform(
            lambda values: values.shift(1).rolling(window=self.window, min_periods=self.window).mean()
        )
        df['rolling_std'] = grouped_metric.transform(
            lambda values: values.shift(1).rolling(window=self.window, min_periods=self.window).std()
        )

        df[f'{metric}_zscore'] = (df[metric] - df['rolling_mean']) / df['rolling_std']
        df[f'{metric}_zscore'] = df[f'{metric}_zscore'].replace([float("inf"), float("-inf")], 0)
        df[f'{metric}_zscore'] = df[f'{metric}_zscore'].fillna(0)
        df[f'{metric}_anomaly'] = df[f'{metric}_zscore'].abs() > self.z_threshold

        return df

    def build_anomaly_results(
        self,
        monitoring_df: pd.DataFrame,
        validated_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Adds Z-score, ML residual, combined detector, and incident labels."""
        anomaly_df = monitoring_df.copy()
        anomaly_df["date"] = pd.to_datetime(anomaly_df["date"], errors="coerce")
        anomaly_df = anomaly_df.sort_values(["date", *BUSINESS_KEY[1:]]).reset_index(drop=True)

        anomaly_df = self._add_zscore_detector(anomaly_df)
        anomaly_df = self._add_ml_residual_detector(anomaly_df)
        anomaly_df = self._add_combined_detector(anomaly_df)
        anomaly_df = self._join_incident_labels(anomaly_df, validated_df)

        anomaly_df["date"] = anomaly_df["date"].dt.strftime("%Y-%m-%d")
        return anomaly_df[ANOMALY_OUTPUT_COLUMNS]

    def _add_zscore_detector(self, df: pd.DataFrame) -> pd.DataFrame:
        warning_threshold = float(self.anomaly_config.get("z_score_warning_threshold", 2.0))
        critical_threshold = float(self.anomaly_config.get("z_score_critical_threshold", 3.0))
        rolling_window = int(self.anomaly_config.get("rolling_window", 28))
        min_periods = int(self.anomaly_config.get("min_periods", 7))

        grouped = df.groupby(BUSINESS_KEY[1:], sort=False)["actual_value"]
        rolling_std = grouped.transform(
            lambda values: values.shift(1).rolling(
                window=rolling_window,
                min_periods=min_periods,
            ).std()
        )

        df["z_score"] = (df["actual_value"] - df["moving_baseline"]) / rolling_std
        df["z_score"] = df["z_score"].replace([float("inf"), float("-inf")], pd.NA)
        df["z_score"] = df["z_score"].where(rolling_std.ne(0))
        abs_z = df["z_score"].abs()
        df["zscore_severity"] = "NORMAL"
        df.loc[abs_z >= warning_threshold, "zscore_severity"] = "WARNING"
        df.loc[abs_z >= critical_threshold, "zscore_severity"] = "CRITICAL"
        df["zscore_anomaly"] = df["zscore_severity"] != "NORMAL"
        return df

    def _add_ml_residual_detector(self, df: pd.DataFrame) -> pd.DataFrame:
        model_config = self.anomaly_config.get("model", {})
        random_state = int(model_config.get("random_state", 42))
        train_fraction = float(model_config.get("train_fraction", 0.70))
        warning_threshold = float(self.anomaly_config.get("residual_warning_threshold_pct", 0.12))
        critical_threshold = float(self.anomaly_config.get("residual_critical_threshold_pct", 0.25))

        feature_df = self._build_model_features(df)
        dates = df["date"].sort_values().drop_duplicates().reset_index(drop=True)
        split_index = max(1, min(len(dates) - 1, int(len(dates) * train_fraction)))
        split_date = dates.iloc[split_index]
        train_mask = df["date"] < split_date

        y = df["actual_value"].astype(float)
        model_name, model_class = self._select_residual_model()
        predicted = pd.Series(index=df.index, dtype=float)

        for kpi_name, group_index in df.groupby("kpi_name").groups.items():
            group_index = pd.Index(group_index)
            group_train_mask = train_mask.loc[group_index]
            group_features = feature_df.loc[group_index]
            group_y = y.loc[group_index]

            if model_name == "xgboost_xgbregressor":
                model = model_class(
                    n_estimators=int(model_config.get("n_estimators", 80)),
                    max_depth=int(model_config.get("max_depth", 3)),
                    learning_rate=float(model_config.get("learning_rate", 0.08)),
                    subsample=float(model_config.get("subsample", 0.9)),
                    colsample_bytree=float(model_config.get("colsample_bytree", 0.9)),
                    objective="reg:squarederror",
                    random_state=random_state,
                    n_jobs=1,
                )
                model.fit(group_features.loc[group_train_mask], group_y.loc[group_train_mask])
                group_predicted = model.predict(group_features)
            elif model_name == "sklearn_hist_gradient_boosting_regressor":
                group_predicted = self._fit_predict_sklearn_hist_gradient(
                    group_features,
                    group_y,
                    group_train_mask,
                    model_config,
                    random_state,
                )
            else:
                group_predicted = self._fit_predict_numpy_ridge(
                    group_features,
                    group_y,
                    group_train_mask,
                    alpha=float(model_config.get("ridge_alpha", 1.0)),
                )

            predicted.loc[group_index] = group_predicted

        predicted = predicted.sort_index().to_numpy()

        df["predicted_value"] = predicted
        df["residual"] = df["actual_value"] - df["predicted_value"]
        df["residual_percent"] = df["residual"] / df["predicted_value"]
        df["residual_percent"] = df["residual_percent"].mask(df["predicted_value"] == 0)
        df["residual_percent"] = df["residual_percent"].replace([float("inf"), float("-inf")], pd.NA)

        direction = df["kpi_name"].map(self._kpi_directions())
        residual_percent = df["residual_percent"]
        lower_bad = direction.eq("lower_is_bad")
        higher_bad = direction.eq("higher_is_bad")

        warning_mask = (
            (lower_bad & (residual_percent <= -warning_threshold))
            | (higher_bad & (residual_percent >= warning_threshold))
        )
        critical_mask = (
            (lower_bad & (residual_percent <= -critical_threshold))
            | (higher_bad & (residual_percent >= critical_threshold))
        )

        df["residual_severity"] = "NORMAL"
        df.loc[warning_mask, "residual_severity"] = "WARNING"
        df.loc[critical_mask, "residual_severity"] = "CRITICAL"
        df["residual_anomaly"] = df["residual_severity"] != "NORMAL"
        self.residual_model_used = model_name
        self.residual_train_split_date = pd.Timestamp(split_date).strftime("%Y-%m-%d")
        return df

    @staticmethod
    def _select_residual_model():
        try:
            from xgboost import XGBRegressor
            return "xgboost_xgbregressor", XGBRegressor
        except Exception:
            try:
                from sklearn.ensemble import HistGradientBoostingRegressor
                return "sklearn_hist_gradient_boosting_regressor", HistGradientBoostingRegressor
            except Exception:
                return "numpy_ridge_regression_residual", None

    def _fit_predict_sklearn_hist_gradient(
        self,
        feature_df: pd.DataFrame,
        y: pd.Series,
        train_mask: pd.Series,
        model_config: dict,
        random_state: int,
    ) -> np.ndarray:
        from sklearn.ensemble import HistGradientBoostingRegressor

        model = HistGradientBoostingRegressor(
            max_iter=int(model_config.get("max_iter", 120)),
            learning_rate=float(model_config.get("learning_rate", 0.08)),
            random_state=random_state,
        )
        model.fit(feature_df.loc[train_mask], y.loc[train_mask])
        return model.predict(feature_df)

    @staticmethod
    def _fit_predict_numpy_ridge(
        feature_df: pd.DataFrame,
        y: pd.Series,
        train_mask: pd.Series,
        alpha: float = 1.0,
    ) -> np.ndarray:
        x_train = feature_df.loc[train_mask].astype(float).to_numpy()
        y_train = y.loc[train_mask].astype(float).to_numpy()
        x_all = feature_df.astype(float).to_numpy()

        train_mean = x_train.mean(axis=0)
        train_std = x_train.std(axis=0)
        train_std[train_std == 0] = 1.0

        x_train_scaled = (x_train - train_mean) / train_std
        x_all_scaled = (x_all - train_mean) / train_std
        x_train_design = np.column_stack([np.ones(len(x_train_scaled)), x_train_scaled])
        x_all_design = np.column_stack([np.ones(len(x_all_scaled)), x_all_scaled])

        penalty = np.eye(x_train_design.shape[1]) * alpha
        penalty[0, 0] = 0.0
        coefficients = np.linalg.solve(
            x_train_design.T @ x_train_design + penalty,
            x_train_design.T @ y_train,
        )
        predicted = x_all_design @ coefficients
        return predicted

    def _add_combined_detector(self, df: pd.DataFrame) -> pd.DataFrame:
        severity_rank = {"NORMAL": 0, "WARNING": 1, "CRITICAL": 2}
        rank_severity = {value: key for key, value in severity_rank.items()}
        z_rank = df["zscore_severity"].map(severity_rank).fillna(0)
        residual_rank = df["residual_severity"].map(severity_rank).fillna(0)
        combined_rank = z_rank.combine(residual_rank, max)

        df["combined_anomaly"] = df["zscore_anomaly"] | df["residual_anomaly"]
        df["combined_severity"] = combined_rank.map(rank_severity)
        return df

    def _join_incident_labels(self, anomaly_df: pd.DataFrame, validated_df: pd.DataFrame) -> pd.DataFrame:
        labels = validated_df.copy()
        labels["date"] = pd.to_datetime(labels["date"], errors="coerce")
        labels = labels[BUSINESS_KEY + LABEL_COLUMNS]
        labels["is_incident"] = labels["is_incident"].map({
            True: True,
            False: False,
            "True": True,
            "False": False,
            "true": True,
            "false": False,
            "1": True,
            "0": False,
            1: True,
            0: False,
        }).fillna(False).astype(bool)

        merged = anomaly_df.merge(labels, on=BUSINESS_KEY, how="left")
        merged["is_incident"] = merged["is_incident"].fillna(False).astype(bool)
        for column in ["incident_id", "incident_type", "incident_description"]:
            merged[column] = merged[column].fillna("")
        return merged

    def _build_model_features(self, df: pd.DataFrame) -> pd.DataFrame:
        feature_source = df[[
            "date",
            "kpi_name",
            "region",
            "device_type",
            "browser",
            "channel",
            "business_segment",
            "moving_baseline",
        ]].copy()
        feature_source["date"] = pd.to_datetime(feature_source["date"], errors="coerce")
        min_date = feature_source["date"].min()
        feature_source["days_since_start"] = (feature_source["date"] - min_date).dt.days
        feature_source["day_of_week"] = feature_source["date"].dt.dayofweek
        feature_source["month"] = feature_source["date"].dt.month
        feature_source = feature_source.drop(columns=["date"])

        numeric_columns = [
            "moving_baseline",
            "days_since_start",
            "day_of_week",
            "month",
        ]
        for column in numeric_columns:
            feature_source[column] = pd.to_numeric(feature_source[column], errors="coerce")
            feature_source[column] = feature_source[column].fillna(feature_source[column].median())

        categorical_columns = [
            "kpi_name",
            "region",
            "device_type",
            "browser",
            "channel",
            "business_segment",
        ]
        return pd.get_dummies(feature_source, columns=categorical_columns, dtype=int)

    def _kpi_directions(self) -> dict:
        thresholds = self.config.get("kpi_monitoring", {}).get("thresholds", {})
        return {
            kpi_name: values.get("direction", "lower_is_bad")
            for kpi_name, values in thresholds.items()
        }

    @staticmethod
    def _load_config(config_path: str) -> dict:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
