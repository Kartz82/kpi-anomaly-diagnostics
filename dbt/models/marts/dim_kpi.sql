with kpies as (
    select distinct kpi_name
    from {{ ref('stg_kpi_daily_metrics') }}
)
select
    row_number() over (order by kpi_name) as kpi_key,
    kpi_name,
    case
        when kpi_name in ('conversion_rate', 'click_through_rate') then 'engagement_metric'
        when kpi_name = 'average_order_value' then 'monetization_metric'
        when kpi_name = 'latency_ms' then 'performance_metric'
        when kpi_name = 'revenue_per_session' then 'monetization_metric'
        else 'other'
    end as kpi_family,
    case
        when kpi_name = 'latency_ms' then 'higher_is_bad'
        else 'lower_is_bad'
    end as direction,
    case
        when kpi_name = 'latency_ms' then 'milliseconds'
        when kpi_name = 'average_order_value' then 'currency'
        when kpi_name = 'revenue_per_session' then 'currency'
        else 'ratio'
    end as measure_unit,
    initcap(replace(kpi_name, '_', ' ')) as description
from kpies

