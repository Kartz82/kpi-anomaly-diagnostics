import pandas as pd
import numpy as np
import yaml
from datetime import datetime, timedelta
from pathlib import Path

class DataIngestor:
    def __init__(
        self,
        config_path: str = "config/monitoring_config.yaml",
        schema_contract_path: str = "config/schema_contract.yaml",
    ):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.segments = self.config.get('segments', [])
        self.schema_contract_path = schema_contract_path
        self.schema_contract = self._load_schema_contract(schema_contract_path)

    def _load_schema_contract(self, schema_contract_path: str) -> dict:
        path = Path(schema_contract_path)
        if not path.exists():
            return {}
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def load_raw_data(self, raw_path: str = "data/raw/kpi_daily_metrics.csv") -> pd.DataFrame:
        """Loads the persisted raw KPI dataset and applies basic parsing/order cleanup."""
        path = Path(raw_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Raw KPI data not found at {raw_path}. "
                "Run python scripts/generate_raw_data.py first."
            )

        df = pd.read_csv(path, keep_default_na=False)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        if "is_incident" in df.columns:
            df["is_incident"] = df["is_incident"].map({
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

        column_order = self.schema_contract.get("column_order", [])
        if column_order:
            ordered_columns = [col for col in column_order if col in df.columns]
            remaining_columns = [col for col in df.columns if col not in ordered_columns]
            df = df[ordered_columns + remaining_columns]

        return df

    def simulate_data(self, days: int = 30, inject_glitch: bool = False, seed: int | None = None) -> pd.DataFrame:
        """Generates a time-series dataset of KPIs across multiple segments."""
        rng = np.random.default_rng(seed)
        data_list = []
        start_date = datetime.now() - timedelta(days=days)

        # Baseline probabilities
        base_conv = self.config['kpis'][0]['alert_thresholds']['warning'] * 2 # ~10%
        base_ctr = self.config['kpis'][1]['alert_thresholds']['warning'] * 2  # ~8%

        for i in range(days):
            curr_date = start_date + timedelta(days=i)
            
            for device in ['Mobile', 'Desktop']:
                for region in ['NA', 'EMEA', 'APAC']:
                    for browser in ['Chrome', 'Safari', 'Firefox']:
                        
                        # Standard random noise
                        size = rng.integers(1000, 2000)
                        conv_rate = base_conv + rng.normal(0, 0.005)
                        ctr = base_ctr + rng.normal(0, 0.004)
                        latency = 200 + rng.normal(0, 20)

                        # Deterministic incident scenarios for the local diagnostic demo.
                        if inject_glitch and i > (days - 4):
                            if device == 'Mobile' and region == 'EMEA' and browser == 'Safari':
                                conv_rate *= 0.6
                            if device == 'Desktop' and region == 'NA' and browser == 'Chrome':
                                ctr *= 0.55
                            if device == 'Mobile' and region == 'APAC' and browser == 'Firefox':
                                latency += 220

                        clicks = int(size * ctr)
                        conversions = int(size * conv_rate)

                        data_list.append({
                            "date": curr_date.strftime("%Y-%m-%d"),
                            "device_type": device,
                            "region": region,
                            "browser": browser,
                            "impressions": size,
                            "clicks": clicks,
                            "conversions": conversions,
                            "ctr": round(clicks / size, 4),
                            "conversion_rate": round(conversions / size, 4),
                            "latency_ms": latency
                        })

        return pd.DataFrame(data_list)
