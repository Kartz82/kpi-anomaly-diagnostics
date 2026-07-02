select
    analysis_date,
    kpi_name,
    detector_used,
    dimension_type,
    dimension_value,
    actual_value_sum_or_avg,
    expected_value_sum_or_avg,
    degradation_amount,
    contribution_share,
    row_number() over (
        partition by analysis_date, kpi_name, detector_used, dimension_type
        order by contribution_share desc, degradation_amount desc, dimension_value
    ) as contribution_rank,
    anomaly_count,
    severity_max,
    recommended_action
from {{ ref('stg_rca_contributions') }}
where degradation_amount > 0

