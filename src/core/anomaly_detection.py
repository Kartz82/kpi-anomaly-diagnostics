import pandas as pd

class AnomalyDetector:
    def __init__(self, threshold: float = 2.0, window: int = 7):
        self.z_threshold = threshold
        self.window = window

    def detect_anomalies(self, df: pd.DataFrame, metric: str) -> pd.DataFrame:
        """Flags records by comparing each point with the prior rolling baseline."""
        df = df.sort_values('date').copy()
        
        # Group and calculate rolling values explicitly
        group_cols = ['device_type', 'region', 'browser']
        grouped_metric = df.groupby(group_cols)[metric]

        df['rolling_mean'] = grouped_metric.transform(
            lambda values: values.shift(1).rolling(window=self.window, min_periods=self.window).mean()
        )
        df['rolling_std'] = grouped_metric.transform(
            lambda values: values.shift(1).rolling(window=self.window, min_periods=self.window).std()
        )
        
        # Compute Z-Score
        df[f'{metric}_zscore'] = (df[metric] - df['rolling_mean']) / df['rolling_std']
        df[f'{metric}_zscore'] = df[f'{metric}_zscore'].replace([float("inf"), float("-inf")], 0)
        df[f'{metric}_zscore'] = df[f'{metric}_zscore'].fillna(0)
        df[f'{metric}_anomaly'] = df[f'{metric}_zscore'].abs() > self.z_threshold
        
        return df
