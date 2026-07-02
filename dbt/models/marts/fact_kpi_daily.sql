select
    d.date_key,
    k.kpi_key,
    r.region_key,
    dev.device_key,
    b.browser_key,
    c.channel_key,
    s.business_segment_key,
    m.impressions,
    m.clicks,
    m.conversions,
    m.orders,
    m.revenue,
    m.latency_ms,
    m.kpi_value,
    m.is_incident,
    m.incident_id,
    m.incident_type,
    m.incident_description
from {{ ref('stg_kpi_daily_metrics') }} m
join {{ ref('dim_date') }} d on d.date_value = m.date
join {{ ref('dim_kpi') }} k on k.kpi_name = m.kpi_name
join {{ ref('dim_region') }} r on r.region_name = m.region
join {{ ref('dim_device') }} dev on dev.device_type = m.device_type
join {{ ref('dim_browser') }} b on b.browser_name = m.browser
join {{ ref('dim_channel') }} c on c.channel_name = m.channel
join {{ ref('dim_business_segment') }} s on s.business_segment_name = m.business_segment

