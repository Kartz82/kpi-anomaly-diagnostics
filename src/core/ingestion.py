import pandas as pd
import numpy as np
import yaml
from datetime import datetime, timedelta

class DataIngestor:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.segments = self.config['segments']

    def simulate_data(self, days: int = 30, inject_glitch: bool = False) -> pd.DataFrame:
        """Generates a time-series dataset of KPIs across multiple segments."""
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
                        size = np.random.randint(1000, 2000)
                        conv_rate = base_conv + np.random.normal(0, 0.005)
                        ctr = base_ctr + np.random.normal(0, 0.004)
                        latency = 200 + np.random.normal(0, 20)

                        # 🚨 THE GLITCH: Drop Mobile conversion in EMEA by 40% on the last 3 days
                        if inject_glitch and i > (days - 4):
                            if device == 'Mobile' and region == 'EMEA':
                                conv_rate *= 0.6
                                latency += 150 # Spike latency too

                        data_list.append({
                            "date": curr_date.strftime("%Y-%m-%d"),
                            "device_type": device,
                            "region": region,
                            "browser": browser,
                            "impressions": size,
                            "clicks": int(size * ctr),
                            "conversions": int(size * conv_rate),
                            "latency_ms": latency
                        })

        return pd.DataFrame(data_list)