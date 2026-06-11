import pandas as pd

class RootCauseAnalyzer:
    def __init__(self, segments: list):
        self.segments = segments

    def analyze_failure(self, df: pd.DataFrame, metric: str) -> dict:
        """Identifies the specific segment combination driving the anomaly."""
        # Isolate the anomalies flagged by the AnomalyDetector
        anomaly_col = f'{metric}_anomaly'
        zscore_col = f'{metric}_zscore'
        anomalies = df[df[anomaly_col] == True].copy()
        
        if anomalies.empty:
            return {
                "anomaly_detected": False,
                "metric": metric,
                "date": None,
                "primary_offender": None,
                "ranked_anomalies": [],
                "summary": "No significant anomalies detected."
            }

        # Find the row with the most extreme (negative) Z-Score
        anomalies["severity"] = anomalies[zscore_col].abs()
        ranked = anomalies.sort_values("severity", ascending=False)
        worst_case = ranked.iloc[0]

        ranked_anomalies = []
        for _, row in ranked.head(10).iterrows():
            ranked_anomalies.append({
                "date": row["date"],
                "segment": {s: row[s] for s in self.segments},
                "z_score": round(float(row[zscore_col]), 2),
                "actual_value": round(float(row[metric]), 4),
                "rolling_mean": round(float(row["rolling_mean"]), 4)
            })
        
        return {
            "anomaly_detected": True,
            "metric": metric,
            "date": worst_case['date'],
            "primary_offender": {
                "segment": {s: worst_case[s] for s in self.segments},
                "z_score": round(float(worst_case[zscore_col]), 2),
                "actual_value": round(float(worst_case[metric]), 4),
                "rolling_mean": round(float(worst_case["rolling_mean"]), 4)
            },
            "ranked_anomalies": ranked_anomalies,
            "summary": "Anomaly detected and ranked by absolute Z-score severity."
        }
