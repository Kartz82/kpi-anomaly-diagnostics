import pandas as pd
import numpy as np

class AnomalyDetector:
    def __init__(self, threshold: float = 2.0):
        self.z_threshold = threshold

    def detect_anomalies(self, df: pd.DataFrame, metric: str) -> pd.DataFrame:
        """Flags records using explicit rolling calculations to avoid TypeErrors."""
        df = df.sort_values('date').copy()
        
        # Group and calculate rolling values explicitly
        group_cols = ['device_type', 'region', 'browser']
        
        # Create a rolling object
        rolling_obj = df.groupby(group_cols)[metric].rolling(window=7, min_periods=1)
        
        # Extract mean and std, then reset index to align with original df
        df['rolling_mean'] = rolling_obj.mean().reset_index(level=[0,1,2], drop=True)
        df['rolling_std'] = rolling_obj.std().reset_index(level=[0,1,2], drop=True).fillna(0.001)
        
        # Compute Z-Score
        df[f'{metric}_zscore'] = (df[metric] - df['rolling_mean']) / df['rolling_std']
        df[f'{metric}_anomaly'] = df[f'{metric}_zscore'].abs() > self.z_threshold
        
        return df