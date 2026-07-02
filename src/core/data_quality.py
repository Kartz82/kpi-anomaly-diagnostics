import pandas as pd
import yaml
from datetime import datetime, timezone

class DataQualityValidator:
    CHECK_WEIGHTS = {
        "schema": 20,
        "data_types": 15,
        "accepted_values": 10,
        "nulls": 15,
        "duplicates": 10,
        "freshness": 10,
        "completeness": 10,
        "volume": 5,
        "numeric_ranges": 5,
    }

    def __init__(self, config_path: str = "config/schema_contract.yaml"):
        with open(config_path, 'r') as f:
            loaded_config = yaml.safe_load(f)

        if "required_columns" in loaded_config:
            self.config = loaded_config
            self.legacy_mode = False
        else:
            self.config = loaded_config.get("data_quality_checks", {})
            self.legacy_mode = True

    def run_checks(self, df: pd.DataFrame) -> dict:
        """Runs automated health checks and returns a scored validation report."""
        if self.legacy_mode:
            return self._run_legacy_checks(df)

        check_results = {
            "schema": self._check_required_columns(df),
            "data_types": self._check_data_types(df),
            "accepted_values": self._check_accepted_values(df),
            "nulls": self._check_nulls(df),
            "duplicates": self._check_duplicates(df),
            "freshness": self._check_freshness(df),
            "completeness": self._check_completeness(df),
            "volume": self._check_volume(df),
            "numeric_ranges": self._check_numeric_ranges(df),
        }
        health_score = self._calculate_health_score(check_results)
        issues = [
            result["summary"]
            for result in check_results.values()
            if not result["passed"]
        ]

        return {
            "metadata": {
                "validated_at": datetime.now(timezone.utc).isoformat(),
                "dataset_name": self.config.get("dataset", {}).get("name", "unknown"),
                "row_count": int(len(df)),
                "column_count": int(len(df.columns)),
            },
            "status": "PASS" if health_score >= 90 and not issues else "FAIL",
            "is_healthy": bool(health_score >= 90 and not issues),
            "health_score": health_score,
            "issues": issues,
            "checks": check_results,
        }

    def _run_legacy_checks(self, df: pd.DataFrame) -> dict:
        report = {
            "status": "PASS",
            "is_healthy": True,
            "health_score": 100,
            "issues": [],
            "checks": {}
        }

        # Check Volume
        row_count = len(df)
        min_records = self.config['min_daily_records']
        report["checks"]["volume"] = {
            "passed": bool(row_count >= min_records),
            "actual_records": int(row_count),
            "minimum_records": int(min_records)
        }
        if len(df) < self.config['min_daily_records']:
            report["issues"].append("Low volume")
            report["health_score"] -= 30

        # Check Nulls
        null_pct = df.isnull().mean().max()
        max_null_pct = self.config['max_null_percentage']
        report["checks"]["nulls"] = {
            "passed": bool(null_pct <= max_null_pct),
            "max_null_percentage": round(float(null_pct), 4),
            "threshold": float(max_null_pct)
        }
        if null_pct > self.config['max_null_percentage']:
            report["issues"].append(f"High Nulls ({null_pct:.1%})")
            report["health_score"] -= 40

        # Final Verdict
        if report["health_score"] < 70:
            report["is_healthy"] = False
            report["status"] = "FAIL"
            
        return report

    def _calculate_health_score(self, check_results: dict) -> int:
        score = 100.0
        for name, result in check_results.items():
            weight = self.CHECK_WEIGHTS[name]
            score -= weight * (1 - result["score"])
        return max(0, min(100, int(round(score))))

    def _check_required_columns(self, df: pd.DataFrame) -> dict:
        required = self.config.get("required_columns", [])
        missing = [column for column in required if column not in df.columns]
        return {
            "passed": len(missing) == 0,
            "score": 1.0 if not missing else 0.0,
            "missing_columns": missing,
            "required_column_count": len(required),
            "summary": "Required schema present" if not missing else f"Missing required columns: {missing}",
        }

    def _check_data_types(self, df: pd.DataFrame) -> dict:
        failures = {}
        type_rules = self.config.get("data_types", {})

        for column, expected_type in type_rules.items():
            if column not in df.columns:
                continue

            series = df[column]
            if expected_type == "date":
                invalid_count = int(pd.to_datetime(series, errors="coerce").isna().sum())
            elif expected_type == "integer":
                numeric = pd.to_numeric(series, errors="coerce")
                invalid_count = int((numeric.isna() | (numeric % 1 != 0)).sum())
            elif expected_type == "number":
                invalid_count = int(pd.to_numeric(series, errors="coerce").isna().sum())
            elif expected_type == "boolean":
                valid_values = {True, False, "True", "False", "true", "false", "1", "0", 1, 0}
                invalid_count = int((~series.map(lambda value: value in valid_values)).sum())
            else:
                invalid_count = int(series.isna().sum())

            if invalid_count:
                failures[column] = invalid_count

        checked_columns = [column for column in type_rules if column in df.columns]
        total_cells = max(len(df) * max(len(checked_columns), 1), 1)
        invalid_total = sum(failures.values())
        score = max(0.0, 1 - invalid_total / total_cells)
        return {
            "passed": invalid_total == 0,
            "score": score,
            "invalid_count": int(invalid_total),
            "failures": failures,
            "summary": "Data types are parseable" if invalid_total == 0 else f"Data type parse failures: {failures}",
        }

    def _check_accepted_values(self, df: pd.DataFrame) -> dict:
        failures = {}
        accepted_values = self.config.get("accepted_values", {})

        for column, allowed_values in accepted_values.items():
            if column not in df.columns:
                continue
            allowed = set(allowed_values)
            invalid_values = sorted(
                value for value in df[column].dropna().unique().tolist()
                if value not in allowed
            )
            if invalid_values:
                failures[column] = invalid_values[:10]

        return {
            "passed": len(failures) == 0,
            "score": 1.0 if not failures else 0.0,
            "failures": failures,
            "summary": "Accepted value checks passed" if not failures else f"Invalid categorical values: {failures}",
        }

    def _check_nulls(self, df: pd.DataFrame) -> dict:
        required = [column for column in self.config.get("non_null_required", []) if column in df.columns]
        null_counts = {
            column: int(df[column].isna().sum())
            for column in required
            if int(df[column].isna().sum()) > 0
        }
        total_required_cells = max(len(df) * max(len(required), 1), 1)
        null_total = sum(null_counts.values())
        score = max(0.0, 1 - null_total / total_required_cells)
        return {
            "passed": null_total == 0,
            "score": score,
            "null_count": int(null_total),
            "null_counts": null_counts,
            "summary": "No required-field nulls found" if null_total == 0 else f"Required-field nulls found: {null_counts}",
        }

    def _check_duplicates(self, df: pd.DataFrame) -> dict:
        duplicate_key = [column for column in self.config.get("duplicate_key", []) if column in df.columns]
        if not duplicate_key:
            return {
                "passed": False,
                "score": 0.0,
                "duplicate_count": 0,
                "duplicate_key": [],
                "summary": "Duplicate key is not available in the dataset",
            }

        duplicate_mask = df.duplicated(subset=duplicate_key, keep=False)
        duplicate_count = int(duplicate_mask.sum())
        duplicate_rate = duplicate_count / len(df) if len(df) else 0
        return {
            "passed": duplicate_count == 0,
            "score": max(0.0, 1 - duplicate_rate),
            "duplicate_count": duplicate_count,
            "duplicate_rate": round(float(duplicate_rate), 6),
            "duplicate_key": duplicate_key,
            "sample_duplicate_keys": (
                df.loc[duplicate_mask, duplicate_key]
                .head(5)
                .astype(str)
                .to_dict(orient="records")
            ),
            "summary": "No duplicate business keys found" if duplicate_count == 0 else f"Duplicate business-key rows found: {duplicate_count}",
        }

    def _check_freshness(self, df: pd.DataFrame) -> dict:
        max_days = int(self.config.get("freshness", {}).get("max_days_since_latest_date", 999999))
        if "date" not in df.columns:
            return {
                "passed": False,
                "score": 0.0,
                "latest_date": None,
                "days_since_latest_date": None,
                "summary": "Cannot evaluate freshness because date column is missing",
            }

        dates = pd.to_datetime(df["date"], errors="coerce")
        latest_date = dates.max()
        if pd.isna(latest_date):
            return {
                "passed": False,
                "score": 0.0,
                "latest_date": None,
                "days_since_latest_date": None,
                "summary": "Cannot evaluate freshness because all dates are invalid",
            }

        today = pd.Timestamp(datetime.now().date())
        days_since = int((today - latest_date.normalize()).days)
        passed = days_since <= max_days
        return {
            "passed": passed,
            "score": 1.0 if passed else 0.0,
            "latest_date": latest_date.strftime("%Y-%m-%d"),
            "days_since_latest_date": days_since,
            "threshold_days": max_days,
            "summary": "Freshness check passed" if passed else f"Latest data is {days_since} days old",
        }

    def _check_completeness(self, df: pd.DataFrame) -> dict:
        expectation = self.config.get("completeness", {})
        minimum_coverage = float(expectation.get("minimum_date_coverage_pct", 1.0))
        expected_min_days = int(expectation.get("expected_min_days", 0))
        if "date" not in df.columns:
            return {
                "passed": False,
                "score": 0.0,
                "observed_days": 0,
                "coverage_pct": 0.0,
                "summary": "Cannot evaluate completeness because date column is missing",
            }

        dates = pd.to_datetime(df["date"], errors="coerce").dropna()
        observed_days = int(dates.dt.normalize().nunique())
        if dates.empty:
            coverage_pct = 0.0
        else:
            calendar_days = int((dates.max().normalize() - dates.min().normalize()).days) + 1
            coverage_pct = observed_days / max(calendar_days, expected_min_days, 1)

        passed = coverage_pct >= minimum_coverage and observed_days >= expected_min_days
        return {
            "passed": passed,
            "score": min(1.0, max(0.0, coverage_pct / minimum_coverage)) if minimum_coverage else 1.0,
            "observed_days": observed_days,
            "expected_min_days": expected_min_days,
            "coverage_pct": round(float(coverage_pct), 6),
            "minimum_coverage_pct": minimum_coverage,
            "summary": "Date completeness check passed" if passed else "Date completeness below expectation",
        }

    def _check_volume(self, df: pd.DataFrame) -> dict:
        volume_config = self.config.get("volume", {})
        minimum_rows = int(volume_config.get("minimum_rows", 0))
        minimum_rows_per_day = int(volume_config.get("minimum_rows_per_day", 0))
        row_count = len(df)

        if "date" in df.columns:
            per_day = df.groupby(pd.to_datetime(df["date"], errors="coerce").dt.normalize()).size()
            min_observed_per_day = int(per_day.min()) if not per_day.empty else 0
        else:
            min_observed_per_day = 0

        passed = row_count >= minimum_rows and min_observed_per_day >= minimum_rows_per_day
        row_score = min(1.0, row_count / minimum_rows) if minimum_rows else 1.0
        daily_score = min(1.0, min_observed_per_day / minimum_rows_per_day) if minimum_rows_per_day else 1.0
        return {
            "passed": passed,
            "score": min(row_score, daily_score),
            "row_count": int(row_count),
            "minimum_rows": minimum_rows,
            "minimum_rows_per_day": minimum_rows_per_day,
            "minimum_observed_rows_per_day": min_observed_per_day,
            "summary": "Volume check passed" if passed else "Volume below configured expectation",
        }

    def _check_numeric_ranges(self, df: pd.DataFrame) -> dict:
        failures = {}
        range_rules = self.config.get("numeric_ranges", {})

        for column, bounds in range_rules.items():
            if column not in df.columns:
                continue
            numeric = pd.to_numeric(df[column], errors="coerce")
            invalid_mask = pd.Series(False, index=df.index)
            if "min" in bounds:
                invalid_mask = invalid_mask | (numeric < bounds["min"])
            if "max" in bounds:
                invalid_mask = invalid_mask | (numeric > bounds["max"])
            invalid_mask = invalid_mask | numeric.isna()
            invalid_count = int(invalid_mask.sum())
            if invalid_count:
                failures[column] = invalid_count

        checked_columns = [column for column in range_rules if column in df.columns]
        total_cells = max(len(df) * max(len(checked_columns), 1), 1)
        invalid_total = sum(failures.values())
        score = max(0.0, 1 - invalid_total / total_cells)
        return {
            "passed": invalid_total == 0,
            "score": score,
            "invalid_count": int(invalid_total),
            "failures": failures,
            "summary": "Numeric range checks passed" if invalid_total == 0 else f"Numeric range failures: {failures}",
        }
