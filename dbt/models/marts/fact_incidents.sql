select
    i.incident_id,
    d.date_key as incident_date_key,
    k.kpi_key,
    i.severity,
    i.confidence_score,
    i.confidence_label,
    i.detector_used,
    i.anomaly_count,
    i.top_root_cause,
    i.recommended_action
from {{ ref('int_incident_enriched') }} i
join {{ ref('dim_date') }} d on d.date_value = i.incident_date
join {{ ref('dim_kpi') }} k on k.kpi_name = i.kpi_name

