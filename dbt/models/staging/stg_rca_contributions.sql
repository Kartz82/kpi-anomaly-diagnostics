select
    cast(analysis_date as date) as analysis_date,
    cast(kpi_name as text) as kpi_name,
    cast(detector_used as text) as detector_used,
    cast(dimension_type as text) as dimension_type,
    cast(dimension_value as text) as dimension_value,
    cast(actual_value_sum_or_avg as double precision) as actual_value_sum_or_avg,
    cast(expected_value_sum_or_avg as double precision) as expected_value_sum_or_avg,
    cast(degradation_amount as double precision) as degradation_amount,
    cast(contribution_share as double precision) as contribution_share,
    cast(contribution_rank as integer) as contribution_rank,
    cast(anomaly_count as integer) as anomaly_count,
    cast(severity_max as text) as severity_max,
    cast(recommended_action as text) as recommended_action
from {{ source('raw', 'raw_rca_contributions') }}

