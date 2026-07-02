with browsers as (
    select distinct browser
    from {{ ref('stg_kpi_daily_metrics') }}
)
select
    row_number() over (order by browser) as browser_key,
    browser as browser_name
from browsers

