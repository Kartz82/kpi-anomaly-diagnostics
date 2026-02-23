-- Identify the 10 worst performing segments by Conversion Rate drop
SELECT 
    observation_date,
    region,
    device_type,
    (CAST(conversions AS FLOAT) / NULLIF(clicks, 0)) AS conv_rate,
    LAG(CAST(conversions AS FLOAT) / NULLIF(clicks, 0)) OVER (
        PARTITION BY region, device_type ORDER BY observation_date
    ) AS prev_day_conv_rate
FROM daily_kpi_metrics
ORDER BY (conv_rate - prev_day_conv_rate) ASC
LIMIT 10;