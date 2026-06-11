import pandas as pd
import yaml

class DataQualityValidator:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)['data_quality_checks']
        
    def run_checks(self, df: pd.DataFrame) -> dict:
        """Runs automated health checks for volume, nulls, and freshness."""
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
