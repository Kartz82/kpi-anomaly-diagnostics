select
    date,
    kpi_name,
    region,
    device_type,
    browser,
    channel,
    business_segment,
    actual_value,
    expected_value,
    moving_baseline,
    percent_variance,
    monitoring_status,
    threshold_breached,
    z_score,
    zscore_anomaly,
    zscore_severity,
    predicted_value,
    residual,
    residual_percent,
    residual_anomaly,
    residual_severity,
    combined_anomaly,
    combined_severity,
    is_incident,
    incident_id,
    incident_type,
    incident_description,
    case
        when residual_anomaly then residual_severity
        when combined_anomaly then combined_severity
        else monitoring_status
    end as analysis_severity,
    case
        when residual_anomaly then 'residual_anomaly'
        when combined_anomaly then 'combined_anomaly'
        when zscore_anomaly then 'zscore_anomaly'
        else 'threshold_breached'
    end as analysis_detector
from {{ ref('stg_anomaly_results') }}

