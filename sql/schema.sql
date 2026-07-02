-- Phase 6A PostgreSQL warehouse schema.
-- Raw tables mirror the exported CSV outputs.
-- Analytics tables form a compact star schema for BI and dashboard use.

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS marts;

CREATE TABLE IF NOT EXISTS raw.raw_kpi_daily_metrics (
    date DATE NOT NULL,
    kpi_name TEXT NOT NULL,
    region TEXT NOT NULL,
    device_type TEXT NOT NULL,
    browser TEXT NOT NULL,
    channel TEXT NOT NULL,
    business_segment TEXT NOT NULL,
    impressions INTEGER NOT NULL,
    clicks INTEGER NOT NULL,
    conversions INTEGER NOT NULL,
    orders INTEGER NOT NULL,
    revenue DOUBLE PRECISION NOT NULL,
    latency_ms DOUBLE PRECISION NOT NULL,
    kpi_value DOUBLE PRECISION NOT NULL,
    is_incident BOOLEAN NOT NULL,
    incident_id TEXT,
    incident_type TEXT,
    incident_description TEXT,
    PRIMARY KEY (date, kpi_name, region, device_type, browser, channel, business_segment)
);

CREATE TABLE IF NOT EXISTS raw.raw_kpi_monitoring (
    date DATE NOT NULL,
    kpi_name TEXT NOT NULL,
    region TEXT NOT NULL,
    device_type TEXT NOT NULL,
    browser TEXT NOT NULL,
    channel TEXT NOT NULL,
    business_segment TEXT NOT NULL,
    actual_value DOUBLE PRECISION NOT NULL,
    rolling_avg_7d DOUBLE PRECISION,
    rolling_avg_14d DOUBLE PRECISION,
    rolling_avg_28d DOUBLE PRECISION,
    moving_baseline DOUBLE PRECISION,
    expected_value DOUBLE PRECISION,
    absolute_variance DOUBLE PRECISION,
    percent_variance DOUBLE PRECISION,
    threshold_value DOUBLE PRECISION,
    threshold_direction TEXT NOT NULL,
    threshold_breached BOOLEAN NOT NULL,
    monitoring_status TEXT NOT NULL,
    PRIMARY KEY (date, kpi_name, region, device_type, browser, channel, business_segment)
);

CREATE TABLE IF NOT EXISTS raw.raw_anomaly_results (
    date DATE NOT NULL,
    kpi_name TEXT NOT NULL,
    region TEXT NOT NULL,
    device_type TEXT NOT NULL,
    browser TEXT NOT NULL,
    channel TEXT NOT NULL,
    business_segment TEXT NOT NULL,
    actual_value DOUBLE PRECISION NOT NULL,
    expected_value DOUBLE PRECISION,
    moving_baseline DOUBLE PRECISION,
    percent_variance DOUBLE PRECISION,
    monitoring_status TEXT NOT NULL,
    threshold_breached BOOLEAN NOT NULL,
    z_score DOUBLE PRECISION,
    zscore_anomaly BOOLEAN NOT NULL,
    zscore_severity TEXT NOT NULL,
    predicted_value DOUBLE PRECISION,
    residual DOUBLE PRECISION,
    residual_percent DOUBLE PRECISION,
    residual_anomaly BOOLEAN NOT NULL,
    residual_severity TEXT NOT NULL,
    combined_anomaly BOOLEAN NOT NULL,
    combined_severity TEXT NOT NULL,
    is_incident BOOLEAN NOT NULL,
    incident_id TEXT,
    incident_type TEXT,
    incident_description TEXT,
    PRIMARY KEY (date, kpi_name, region, device_type, browser, channel, business_segment)
);

CREATE TABLE IF NOT EXISTS raw.raw_rca_contributions (
    analysis_date DATE NOT NULL,
    kpi_name TEXT NOT NULL,
    detector_used TEXT NOT NULL,
    dimension_type TEXT NOT NULL,
    dimension_value TEXT NOT NULL,
    actual_value_sum_or_avg DOUBLE PRECISION NOT NULL,
    expected_value_sum_or_avg DOUBLE PRECISION NOT NULL,
    degradation_amount DOUBLE PRECISION NOT NULL,
    contribution_share DOUBLE PRECISION NOT NULL,
    contribution_rank INTEGER NOT NULL,
    anomaly_count INTEGER NOT NULL,
    severity_max TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    PRIMARY KEY (analysis_date, kpi_name, detector_used, dimension_type, dimension_value)
);

CREATE TABLE IF NOT EXISTS raw.raw_incident_history (
    incident_id TEXT PRIMARY KEY,
    date DATE NOT NULL,
    kpi_affected TEXT NOT NULL,
    severity TEXT NOT NULL,
    confidence_label TEXT NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL,
    top_root_cause TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    detector_used TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.dim_date (
    date_key INTEGER PRIMARY KEY,
    date_value DATE NOT NULL UNIQUE,
    year SMALLINT NOT NULL,
    quarter SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    day SMALLINT NOT NULL,
    day_of_week SMALLINT NOT NULL,
    day_name TEXT NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.dim_kpi (
    kpi_key INTEGER PRIMARY KEY,
    kpi_name TEXT NOT NULL UNIQUE,
    kpi_family TEXT NOT NULL,
    direction TEXT NOT NULL,
    measure_unit TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.dim_region (
    region_key INTEGER PRIMARY KEY,
    region_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS analytics.dim_device (
    device_key INTEGER PRIMARY KEY,
    device_type TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS analytics.dim_browser (
    browser_key INTEGER PRIMARY KEY,
    browser_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS analytics.dim_channel (
    channel_key INTEGER PRIMARY KEY,
    channel_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS analytics.dim_business_segment (
    business_segment_key INTEGER PRIMARY KEY,
    business_segment_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS analytics.fact_kpi_daily (
    date_key INTEGER NOT NULL REFERENCES analytics.dim_date(date_key),
    kpi_key INTEGER NOT NULL REFERENCES analytics.dim_kpi(kpi_key),
    region_key INTEGER NOT NULL REFERENCES analytics.dim_region(region_key),
    device_key INTEGER NOT NULL REFERENCES analytics.dim_device(device_key),
    browser_key INTEGER NOT NULL REFERENCES analytics.dim_browser(browser_key),
    channel_key INTEGER NOT NULL REFERENCES analytics.dim_channel(channel_key),
    business_segment_key INTEGER NOT NULL REFERENCES analytics.dim_business_segment(business_segment_key),
    impressions INTEGER NOT NULL,
    clicks INTEGER NOT NULL,
    conversions INTEGER NOT NULL,
    orders INTEGER NOT NULL,
    revenue DOUBLE PRECISION NOT NULL,
    latency_ms DOUBLE PRECISION NOT NULL,
    kpi_value DOUBLE PRECISION NOT NULL,
    is_incident BOOLEAN NOT NULL,
    incident_id TEXT,
    incident_type TEXT,
    incident_description TEXT,
    PRIMARY KEY (date_key, kpi_key, region_key, device_key, browser_key, channel_key, business_segment_key)
);

CREATE INDEX IF NOT EXISTS idx_fact_kpi_daily_kpi_date
    ON analytics.fact_kpi_daily (kpi_key, date_key);

CREATE TABLE IF NOT EXISTS analytics.fact_kpi_monitoring (
    date_key INTEGER NOT NULL REFERENCES analytics.dim_date(date_key),
    kpi_key INTEGER NOT NULL REFERENCES analytics.dim_kpi(kpi_key),
    region_key INTEGER NOT NULL REFERENCES analytics.dim_region(region_key),
    device_key INTEGER NOT NULL REFERENCES analytics.dim_device(device_key),
    browser_key INTEGER NOT NULL REFERENCES analytics.dim_browser(browser_key),
    channel_key INTEGER NOT NULL REFERENCES analytics.dim_channel(channel_key),
    business_segment_key INTEGER NOT NULL REFERENCES analytics.dim_business_segment(business_segment_key),
    actual_value DOUBLE PRECISION NOT NULL,
    rolling_avg_7d DOUBLE PRECISION,
    rolling_avg_14d DOUBLE PRECISION,
    rolling_avg_28d DOUBLE PRECISION,
    moving_baseline DOUBLE PRECISION,
    expected_value DOUBLE PRECISION,
    absolute_variance DOUBLE PRECISION,
    percent_variance DOUBLE PRECISION,
    threshold_value DOUBLE PRECISION,
    threshold_direction TEXT NOT NULL,
    threshold_breached BOOLEAN NOT NULL,
    monitoring_status TEXT NOT NULL,
    PRIMARY KEY (date_key, kpi_key, region_key, device_key, browser_key, channel_key, business_segment_key)
);

CREATE INDEX IF NOT EXISTS idx_fact_kpi_monitoring_kpi_date
    ON analytics.fact_kpi_monitoring (kpi_key, date_key);

CREATE TABLE IF NOT EXISTS analytics.fact_kpi_anomalies (
    date_key INTEGER NOT NULL REFERENCES analytics.dim_date(date_key),
    kpi_key INTEGER NOT NULL REFERENCES analytics.dim_kpi(kpi_key),
    region_key INTEGER NOT NULL REFERENCES analytics.dim_region(region_key),
    device_key INTEGER NOT NULL REFERENCES analytics.dim_device(device_key),
    browser_key INTEGER NOT NULL REFERENCES analytics.dim_browser(browser_key),
    channel_key INTEGER NOT NULL REFERENCES analytics.dim_channel(channel_key),
    business_segment_key INTEGER NOT NULL REFERENCES analytics.dim_business_segment(business_segment_key),
    actual_value DOUBLE PRECISION NOT NULL,
    expected_value DOUBLE PRECISION,
    moving_baseline DOUBLE PRECISION,
    percent_variance DOUBLE PRECISION,
    monitoring_status TEXT NOT NULL,
    threshold_breached BOOLEAN NOT NULL,
    z_score DOUBLE PRECISION,
    zscore_anomaly BOOLEAN NOT NULL,
    zscore_severity TEXT NOT NULL,
    predicted_value DOUBLE PRECISION,
    residual DOUBLE PRECISION,
    residual_percent DOUBLE PRECISION,
    residual_anomaly BOOLEAN NOT NULL,
    residual_severity TEXT NOT NULL,
    combined_anomaly BOOLEAN NOT NULL,
    combined_severity TEXT NOT NULL,
    is_incident BOOLEAN NOT NULL,
    incident_id TEXT,
    incident_type TEXT,
    incident_description TEXT,
    PRIMARY KEY (date_key, kpi_key, region_key, device_key, browser_key, channel_key, business_segment_key)
);

CREATE INDEX IF NOT EXISTS idx_fact_kpi_anomalies_kpi_date
    ON analytics.fact_kpi_anomalies (kpi_key, date_key);

CREATE TABLE IF NOT EXISTS analytics.fact_rca_contributions (
    analysis_date_key INTEGER NOT NULL REFERENCES analytics.dim_date(date_key),
    kpi_key INTEGER NOT NULL REFERENCES analytics.dim_kpi(kpi_key),
    detector_used TEXT NOT NULL,
    dimension_type TEXT NOT NULL,
    dimension_value TEXT NOT NULL,
    actual_value_sum_or_avg DOUBLE PRECISION NOT NULL,
    expected_value_sum_or_avg DOUBLE PRECISION NOT NULL,
    degradation_amount DOUBLE PRECISION NOT NULL,
    contribution_share DOUBLE PRECISION NOT NULL,
    contribution_rank INTEGER NOT NULL,
    anomaly_count INTEGER NOT NULL,
    severity_max TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    PRIMARY KEY (analysis_date_key, kpi_key, detector_used, dimension_type, dimension_value)
);

CREATE INDEX IF NOT EXISTS idx_fact_rca_contributions_kpi_date
    ON analytics.fact_rca_contributions (kpi_key, analysis_date_key);

CREATE TABLE IF NOT EXISTS analytics.fact_incidents (
    incident_id TEXT PRIMARY KEY,
    incident_date_key INTEGER NOT NULL REFERENCES analytics.dim_date(date_key),
    kpi_key INTEGER NOT NULL REFERENCES analytics.dim_kpi(kpi_key),
    severity TEXT NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL,
    confidence_label TEXT NOT NULL,
    detector_used TEXT NOT NULL,
    anomaly_count INTEGER NOT NULL,
    top_root_cause TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    executive_summary TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fact_incidents_kpi_date
    ON analytics.fact_incidents (kpi_key, incident_date_key);

CREATE TABLE IF NOT EXISTS marts.mart_kpi_health (
    date_key INTEGER NOT NULL REFERENCES analytics.dim_date(date_key),
    kpi_key INTEGER NOT NULL REFERENCES analytics.dim_kpi(kpi_key),
    monitored_rows INTEGER NOT NULL,
    normal_rows INTEGER NOT NULL,
    warning_rows INTEGER NOT NULL,
    critical_rows INTEGER NOT NULL,
    breach_rows INTEGER NOT NULL,
    avg_actual_value DOUBLE PRECISION NOT NULL,
    avg_expected_value DOUBLE PRECISION NOT NULL,
    avg_percent_variance DOUBLE PRECISION NOT NULL,
    max_abs_percent_variance DOUBLE PRECISION NOT NULL,
    health_score DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (date_key, kpi_key)
);

CREATE TABLE IF NOT EXISTS marts.mart_incident_summary (
    incident_id TEXT PRIMARY KEY,
    incident_date_key INTEGER NOT NULL REFERENCES analytics.dim_date(date_key),
    kpi_key INTEGER NOT NULL REFERENCES analytics.dim_kpi(kpi_key),
    severity TEXT NOT NULL,
    confidence_label TEXT NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL,
    detector_used TEXT NOT NULL,
    anomaly_count INTEGER NOT NULL,
    top_root_cause TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    executive_summary TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS marts.mart_data_quality_summary (
    run_timestamp TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    health_score INTEGER NOT NULL,
    schema_status TEXT NOT NULL,
    null_issue_count INTEGER NOT NULL,
    duplicate_issue_count INTEGER NOT NULL,
    freshness_status TEXT NOT NULL,
    completeness_status TEXT NOT NULL,
    volume_status TEXT NOT NULL,
    overall_issue_count INTEGER NOT NULL
);

