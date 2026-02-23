/* KPI Monitoring Schema
  This table stores the daily aggregated metrics by segment.
*/

CREATE TABLE daily_kpi_metrics (
    observation_date DATE NOT NULL,
    device_type VARCHAR(50),
    region VARCHAR(50),
    browser VARCHAR(50),
    impressions INTEGER,
    clicks INTEGER,
    conversions INTEGER,
    latency_ms FLOAT,
    PRIMARY KEY (observation_date, device_type, region, browser)
);