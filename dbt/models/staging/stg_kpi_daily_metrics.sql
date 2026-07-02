select
    cast(date as date) as date,
    cast(kpi_name as text) as kpi_name,
    cast(region as text) as region,
    cast(device_type as text) as device_type,
    cast(browser as text) as browser,
    cast(channel as text) as channel,
    cast(business_segment as text) as business_segment,
    cast(impressions as integer) as impressions,
    cast(clicks as integer) as clicks,
    cast(conversions as integer) as conversions,
    cast(orders as integer) as orders,
    cast(revenue as double precision) as revenue,
    cast(latency_ms as double precision) as latency_ms,
    cast(kpi_value as double precision) as kpi_value,
    cast(is_incident as boolean) as is_incident,
    cast(incident_id as text) as incident_id,
    cast(incident_type as text) as incident_type,
    cast(incident_description as text) as incident_description
from {{ source('raw', 'raw_kpi_daily_metrics') }}

