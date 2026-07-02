select
    d.date_key as analysis_date_key,
    k.kpi_key,
    r.detector_used,
    r.dimension_type,
    r.dimension_value,
    r.actual_value_sum_or_avg,
    r.expected_value_sum_or_avg,
    r.degradation_amount,
    r.contribution_share,
    r.contribution_rank,
    r.anomaly_count,
    r.severity_max,
    r.recommended_action
from {{ ref('int_rca_contributions') }} r
join {{ ref('dim_date') }} d on d.date_value = r.analysis_date
join {{ ref('dim_kpi') }} k on k.kpi_name = r.kpi_name

