with devices as (
    select distinct device_type
    from {{ ref('stg_kpi_daily_metrics') }}
)
select
    row_number() over (order by device_type) as device_key,
    device_type
from devices

