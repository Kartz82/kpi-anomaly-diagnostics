select
    cast(date as date) as date,
    cast(kpi_name as text) as kpi_name,
    cast(region as text) as region,
    cast(device_type as text) as device_type,
    cast(browser as text) as browser,
    cast(channel as text) as channel,
    cast(business_segment as text) as business_segment,
    cast(actual_value as double precision) as actual_value,
    cast(rolling_avg_7d as double precision) as rolling_avg_7d,
    cast(rolling_avg_14d as double precision) as rolling_avg_14d,
    cast(rolling_avg_28d as double precision) as rolling_avg_28d,
    cast(moving_baseline as double precision) as moving_baseline,
    cast(expected_value as double precision) as expected_value,
    cast(absolute_variance as double precision) as absolute_variance,
    cast(percent_variance as double precision) as percent_variance,
    cast(threshold_value as double precision) as threshold_value,
    cast(threshold_direction as text) as threshold_direction,
    cast(threshold_breached as boolean) as threshold_breached,
    cast(monitoring_status as text) as monitoring_status
from {{ source('raw', 'raw_kpi_monitoring') }}

