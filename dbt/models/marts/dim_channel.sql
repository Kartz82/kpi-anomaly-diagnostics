with channels as (
    select distinct channel
    from {{ ref('stg_kpi_daily_metrics') }}
)
select
    row_number() over (order by channel) as channel_key,
    channel as channel_name
from channels

