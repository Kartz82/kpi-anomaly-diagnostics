-- Phase 6A SQL proof for portfolio review and README examples.

-- KPI health by day and KPI.
SELECT
    d.date_value AS day,
    k.kpi_name,
    h.monitored_rows,
    h.warning_rows,
    h.critical_rows,
    h.breach_rows,
    h.health_score,
    h.avg_percent_variance
FROM marts.mart_kpi_health h
JOIN analytics.dim_date d ON d.date_key = h.date_key
JOIN analytics.dim_kpi k ON k.kpi_key = h.kpi_key
ORDER BY day DESC, k.kpi_name;

-- Anomaly count by KPI and severity.
SELECT
    k.kpi_name,
    a.combined_severity,
    COUNT(*) AS anomaly_count
FROM analytics.fact_kpi_anomalies a
JOIN analytics.dim_kpi k ON k.kpi_key = a.kpi_key
GROUP BY 1, 2
ORDER BY anomaly_count DESC, k.kpi_name, a.combined_severity;

-- Top RCA contributors by KPI/date.
SELECT
    d.date_value AS analysis_date,
    k.kpi_name,
    r.dimension_type,
    r.dimension_value,
    r.degradation_amount,
    r.contribution_share,
    r.contribution_rank
FROM analytics.fact_rca_contributions r
JOIN analytics.dim_date d ON d.date_key = r.analysis_date_key
JOIN analytics.dim_kpi k ON k.kpi_key = r.kpi_key
WHERE r.contribution_rank <= 3
ORDER BY analysis_date DESC, k.kpi_name, r.contribution_share DESC;

-- Incident summary with confidence and severity.
SELECT
    d.date_value AS incident_date,
    k.kpi_name,
    i.severity,
    i.confidence_label,
    i.confidence_score,
    i.detector_used,
    i.top_root_cause,
    i.recommended_action
FROM marts.mart_incident_summary i
JOIN analytics.dim_date d ON d.date_key = i.incident_date_key
JOIN analytics.dim_kpi k ON k.kpi_key = i.kpi_key
ORDER BY incident_date DESC, i.severity DESC;

-- Data quality and monitoring summary.
SELECT
    q.run_timestamp,
    q.status,
    q.health_score,
    q.schema_status,
    q.null_issue_count,
    q.duplicate_issue_count,
    q.freshness_status,
    q.completeness_status,
    q.volume_status
FROM marts.mart_data_quality_summary q
ORDER BY q.run_timestamp DESC;

-- Executive KPI health rollup.
SELECT
    k.kpi_name,
    COUNT(*) AS monitored_rows,
    SUM(CASE WHEN h.critical_rows > 0 THEN 1 ELSE 0 END) AS critical_days,
    AVG(h.health_score) AS avg_health_score,
    AVG(h.breach_rows::DOUBLE PRECISION / NULLIF(h.monitored_rows, 0)) AS avg_breach_rate
FROM marts.mart_kpi_health h
JOIN analytics.dim_kpi k ON k.kpi_key = h.kpi_key
GROUP BY 1
ORDER BY avg_health_score ASC, k.kpi_name;

-- Dimension drill-down query for root cause.
SELECT
    r.dimension_type,
    r.dimension_value,
    SUM(r.degradation_amount) AS total_degradation,
    SUM(r.contribution_share) AS total_contribution_share
FROM analytics.fact_rca_contributions r
GROUP BY 1, 2
ORDER BY total_degradation DESC, total_contribution_share DESC;

-- Example: Mobile + APAC + Safari contribution to conversion degradation.
SELECT
    d.date_value AS analysis_date,
    r.kpi_key,
    r.dimension_type,
    r.dimension_value,
    r.degradation_amount,
    r.contribution_share,
    r.recommended_action
FROM analytics.fact_rca_contributions r
JOIN analytics.dim_date d ON d.date_key = r.analysis_date_key
JOIN analytics.dim_kpi k ON k.kpi_key = r.kpi_key
WHERE k.kpi_name = 'conversion_rate'
  AND r.dimension_value ILIKE '%APAC%'
  AND r.dimension_value ILIKE '%Mobile%'
  AND r.dimension_value ILIKE '%Safari%'
ORDER BY r.contribution_share DESC;

-- Example: North America + Desktop + Chrome latency incident.
SELECT
    d.date_value AS analysis_date,
    k.kpi_name,
    r.dimension_type,
    r.dimension_value,
    r.degradation_amount,
    r.contribution_share,
    r.recommended_action
FROM analytics.fact_rca_contributions r
JOIN analytics.dim_date d ON d.date_key = r.analysis_date_key
JOIN analytics.dim_kpi k ON k.kpi_key = r.kpi_key
WHERE k.kpi_name = 'latency_ms'
  AND r.dimension_value ILIKE '%North America%'
  AND r.dimension_value ILIKE '%Desktop%'
  AND r.dimension_value ILIKE '%Chrome%'
ORDER BY r.contribution_share DESC;
