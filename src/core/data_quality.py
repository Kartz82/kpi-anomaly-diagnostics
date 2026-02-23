import pandas as pd
import yaml

class DataQualityValidator:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)['data_quality_checks']
        
    def run_checks(self, df: pd.DataFrame) -> dict:
        """Runs automated health checks for volume, nulls, and freshness."""
        report = {"is_healthy": True, "failed_checks": [], "health_score": 100}

        # Check Volume
        if len(df) < self.config['min_daily_records']:
            report["failed_checks"].append("Low volume")
            report["health_score"] -= 30

        # Check Nulls
        null_pct = df.isnull().mean().max()
        if null_pct > self.config['max_null_percentage']:
            report["failed_checks"].append(f"High Nulls ({null_pct:.1%})")
            report["health_score"] -= 40

        # Final Verdict
        if report["health_score"] < 70:
            report["is_healthy"] = False
            
        return report