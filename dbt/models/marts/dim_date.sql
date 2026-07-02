with dates as (
    select distinct cast(date as date) as date_value
    from {{ ref('stg_kpi_daily_metrics') }}
)
select
    (to_char(date_value, 'YYYYMMDD'))::integer as date_key,
    date_value,
    extract(year from date_value)::smallint as year,
    extract(quarter from date_value)::smallint as quarter,
    extract(month from date_value)::smallint as month,
    extract(day from date_value)::smallint as day,
    extract(dow from date_value)::smallint as day_of_week,
    trim(to_char(date_value, 'Day'))::text as day_name,
    (extract(dow from date_value) in (0, 6)) as is_weekend
from dates

