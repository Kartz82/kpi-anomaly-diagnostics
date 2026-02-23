import pandas as pd

class RootCauseAnalyzer:
    def __init__(self, segments: list):
        self.segments = segments

    def analyze_failure(self, df: pd.DataFrame, metric: str) -> dict:
        """Identifies the specific segment combination driving the anomaly."""
        # Isolate the anomalies flagged by the AnomalyDetector
        anomalies = df[df[f'{metric}_anomaly'] == True]
        
        if anomalies.empty:
            return {"status": "No significant anomalies detected."}

        # Find the row with the most extreme (negative) Z-Score
        worst_case = anomalies.sort_values(f'{metric}_zscore').iloc[0]
        
        return {
            "metric": metric,
            "detected_on": worst_case['date'],
            "primary_offender": {
                "segment": {s: worst_case[s] for s in self.segments},
                "z_score": round(worst_case[f'{metric}_zscore'], 2),
                "actual_value": round(float(worst_case[metric]), 4)
            }
        }