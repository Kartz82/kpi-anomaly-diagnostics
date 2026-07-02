select
    d.date_key,
    k.kpi_key,
    r.region_key,
    dev.device_key,
    b.browser_key,
    c.channel_key,
    s.business_segment_key,
    a.actual_value,
    a.expected_value,
    a.moving_baseline,
    a.percent_variance,
    a.monitoring_status,
    a.threshold_breached,
    a.z_score,
    a.zscore_anomaly,
    a.zscore_severity,
    a.predicted_value,
    a.residual,
    a.residual_percent,
    a.residual_anomaly,
    a.residual_severity,
    a.combined_anomaly,
    a.combined_severity,
    a.is_incident,
    a.incident_id,
    a.incident_type,
    a.incident_description
from {{ ref('stg_anomaly_results') }} a
join {{ ref('dim_date') }} d on d.date_value = a.date
join {{ ref('dim_kpi') }} k on k.kpi_name = a.kpi_name
join {{ ref('dim_region') }} r on r.region_name = a.region
join {{ ref('dim_device') }} dev on dev.device_type = a.device_type
join {{ ref('dim_browser') }} b on b.browser_name = a.browser
join {{ ref('dim_channel') }} c on c.channel_name = a.channel
join {{ ref('dim_business_segment') }} s on s.business_segment_name = a.business_segment

