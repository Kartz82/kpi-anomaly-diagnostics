with ranked as (
    select
        analysis_date_key,
        kpi_key,
        detector_used,
        dimension_type,
        dimension_value,
        degradation_amount,
        contribution_share,
        contribution_rank,
        anomaly_count,
        severity_max,
        recommended_action,
        row_number() over (
            partition by analysis_date_key, kpi_key
            order by contribution_share desc, degradation_amount desc
        ) as overall_rank
    from {{ ref('fact_rca_contributions') }}
)
select
    analysis_date_key,
    kpi_key,
    detector_used,
    dimension_type,
    dimension_value,
    degradation_amount,
    contribution_share,
    contribution_rank,
    anomaly_count,
    severity_max,
    recommended_action,
    (
        'For ' || kpi_key || ' on ' || analysis_date_key::text || ', '
        || dimension_value || ' contributed '
        || round((contribution_share * 100)::numeric, 1)::text
        || '% of measured degradation.'
    ) as root_cause_statement
from ranked
where overall_rank = 1
