import pandas as pd
import numpy as np
import yaml
from datetime import datetime, timedelta

class DataIngestor:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.segments = self.config['segments']

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
