select
    incident_id,
    incident_date_key,
    kpi_key,
    severity,
    confidence_label,
    confidence_score,
    detector_used,
    anomaly_count,
    top_root_cause,
    recommended_action
from {{ ref('fact_incidents') }}

