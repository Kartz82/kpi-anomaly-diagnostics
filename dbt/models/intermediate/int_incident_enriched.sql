with incidents as (
    select * from {{ ref('stg_incident_history') }}
),
top_rca as (
    select *
    from {{ ref('int_rca_contributions') }}
    where contribution_rank = 1
),
incident_counts as (
    select
        date,
        kpi_name,
        count(*) as anomaly_count
    from {{ ref('int_anomaly_events') }}
    where residual_anomaly
    group by 1, 2
),
ranked as (
    select
        i.incident_id,
        i.incident_date,
        i.kpi_name,
        i.severity,
        i.confidence_label,
        i.confidence_score,
        i.detector_used,
        coalesce(c.anomaly_count, 1) as anomaly_count,
        coalesce(r.dimension_value, i.top_root_cause) as top_root_cause,
        coalesce(r.dimension_type, 'incident_history') as top_dimension_type,
        coalesce(r.contribution_share, 0) as top_contribution_share,
        coalesce(r.recommended_action, i.recommended_action) as recommended_action,
        row_number() over (
            partition by i.incident_id
            order by coalesce(r.contribution_share, 0) desc,
                     coalesce(r.degradation_amount, 0) desc,
                     coalesce(r.dimension_type, 'incident_history')
        ) as incident_rank
    from incidents i
    left join top_rca r
        on i.incident_date = r.analysis_date
       and i.kpi_name = r.kpi_name
       and i.detector_used = r.detector_used
    left join incident_counts c
        on i.incident_date = c.date
       and i.kpi_name = c.kpi_name
)
select
    incident_id,
    incident_date,
    kpi_name,
    severity,
    confidence_label,
    confidence_score,
    detector_used,
    anomaly_count,
    top_root_cause,
    top_dimension_type,
    top_contribution_share,
    recommended_action
from ranked
where incident_rank = 1
