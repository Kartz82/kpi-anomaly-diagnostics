select
    cast(date as date) as incident_date,
    cast(kpi_affected as text) as kpi_name,
    cast(severity as text) as severity,
    cast(confidence_label as text) as confidence_label,
    cast(confidence_score as double precision) as confidence_score,
    cast(top_root_cause as text) as top_root_cause,
    cast(recommended_action as text) as recommended_action,
    cast(detector_used as text) as detector_used,
    cast(incident_id as text) as incident_id
from {{ source('raw', 'raw_incident_history') }}

