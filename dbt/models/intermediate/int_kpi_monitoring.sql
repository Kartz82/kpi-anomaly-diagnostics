with monitoring as (
    select * from {{ ref('stg_kpi_monitoring') }}
)
select
    date,
    kpi_name,
    count(*) as monitored_rows,
    sum(case when monitoring_status = 'NORMAL' then 1 else 0 end) as normal_rows,
    sum(case when monitoring_status = 'WARNING' then 1 else 0 end) as warning_rows,
    sum(case when monitoring_status = 'CRITICAL' then 1 else 0 end) as critical_rows,
    sum(case when threshold_breached then 1 else 0 end) as breach_rows,
    avg(actual_value) as avg_actual_value,
    avg(expected_value) as avg_expected_value,
    avg(percent_variance) as avg_percent_variance,
    max(abs(percent_variance)) as max_abs_percent_variance,
    greatest(
        0,
        least(
            100,
            100 - (
                (sum(case when monitoring_status = 'WARNING' then 1 else 0 end) * 0.5)
                + (sum(case when monitoring_status = 'CRITICAL' then 1 else 0 end) * 1.5)
            ) / nullif(count(*), 0) * 100
        )
    ) as health_score
from monitoring
group by 1, 2

