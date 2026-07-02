with segments as (
    select distinct business_segment
    from {{ ref('stg_kpi_daily_metrics') }}
)
select
    row_number() over (order by business_segment) as business_segment_key,
    business_segment as business_segment_name
from segments

