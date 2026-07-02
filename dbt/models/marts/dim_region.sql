with regions as (
    select distinct region
    from {{ ref('stg_kpi_daily_metrics') }}
)
select
    row_number() over (order by region) as region_key,
    region as region_name
from regions

