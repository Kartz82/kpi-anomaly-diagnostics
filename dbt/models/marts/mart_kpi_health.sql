select
    d.date_key,
    k.kpi_key,
    h.monitored_rows,
    h.normal_rows,
    h.warning_rows,
    h.critical_rows,
    h.breach_rows,
    h.avg_actual_value,
    h.avg_expected_value,
    h.avg_percent_variance,
    h.max_abs_percent_variance,
    h.health_score
from {{ ref('int_kpi_monitoring') }} h
join {{ ref('dim_date') }} d
    on d.date_value = h.date
join {{ ref('dim_kpi') }} k
    on k.kpi_name = h.kpi_name
