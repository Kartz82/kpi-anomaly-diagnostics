from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_OUTPUT_PATH = Path("data/raw/kpi_daily_metrics.csv")
DEFAULT_SEED = 20260702
DEFAULT_END_DATE = "2026-06-30"
DEFAULT_DAYS = 150

REGIONS = ["North America", "EMEA", "APAC"]
DEVICE_TYPES = ["Desktop", "Mobile"]
BROWSERS = ["Chrome", "Safari", "Firefox"]
CHANNELS = ["Organic", "Paid Search", "Email"]
BUSINESS_SEGMENTS = ["SMB", "Mid-Market", "Enterprise"]
KPI_NAMES = [
    "conversion_rate",
    "click_through_rate",
    "average_order_value",
    "latency_ms",
    "revenue_per_session",
]


# Injected incident windows, expressed as day offsets back from the dataset's end date
# rather than as absolute dates.
#
# Offsets, not literals, because the end date is a parameter: generating with
# --end-date today must move the incidents with the data. With absolute dates the
# incidents would drift out of the generated window entirely and the labelled ground
# truth would silently vanish.
#
# With the default end date of 2026-06-30 these resolve to exactly the original
# windows (2026-06-05..06-14, 2026-05-18..05-25, 2026-06-18..06-27), so the default
# output is unchanged.
INCIDENT_WINDOWS_DAYS_BEFORE_END = {
    "conversion_rate_degradation": (25, 16),
    "latency_spike": (43, 36),
    "revenue_per_session_degradation": (12, 3),
}


def _window(end_date: pd.Timestamp, key: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    start_offset, end_offset = INCIDENT_WINDOWS_DAYS_BEFORE_END[key]
    return (
        end_date - pd.Timedelta(days=start_offset),
        end_date - pd.Timedelta(days=end_offset),
    )


def _incident_for_row(
    date: pd.Timestamp,
    kpi_name: str,
    region: str,
    device_type: str,
    browser: str,
    channel: str,
    business_segment: str,
    end_date: pd.Timestamp,
) -> dict[str, object]:
    incidents = []

    cr_start, cr_end = _window(end_date, "conversion_rate_degradation")
    if (
        cr_start <= date <= cr_end
        and kpi_name == "conversion_rate"
        and device_type == "Mobile"
        and region == "APAC"
        and browser == "Safari"
    ):
        incidents.append((
            "INC-CR-APAC-MOBILE-SAFARI",
            "conversion_rate_degradation",
            "Conversion rate degradation affecting Mobile + APAC + Safari.",
        ))

    lat_start, lat_end = _window(end_date, "latency_spike")
    if (
        lat_start <= date <= lat_end
        and kpi_name == "latency_ms"
        and device_type == "Desktop"
        and region == "North America"
        and browser == "Chrome"
    ):
        incidents.append((
            "INC-LATENCY-NA-DESKTOP-CHROME",
            "latency_spike",
            "Latency spike affecting Desktop + North America + Chrome.",
        ))

    rps_start, rps_end = _window(end_date, "revenue_per_session_degradation")
    if (
        rps_start <= date <= rps_end
        and kpi_name == "revenue_per_session"
        and channel == "Paid Search"
        and business_segment == "Enterprise"
    ):
        incidents.append((
            "INC-RPS-PAID-ENTERPRISE",
            "revenue_per_session_degradation",
            "Revenue per session degradation affecting Paid Search + Enterprise.",
        ))

    if not incidents:
        return {
            "is_incident": False,
            "incident_id": "",
            "incident_type": "",
            "incident_description": "",
        }

    return {
        "is_incident": True,
        "incident_id": "|".join(item[0] for item in incidents),
        "incident_type": "|".join(item[1] for item in incidents),
        "incident_description": " ".join(item[2] for item in incidents),
    }


def _base_metrics(
    rng: np.random.Generator,
    date_index: int,
    region: str,
    device_type: str,
    browser: str,
    channel: str,
    business_segment: str,
) -> dict[str, float]:
    weekly = np.sin(2 * np.pi * date_index / 7)
    trend = date_index / 1000

    region_factor = {
        "North America": 1.08,
        "EMEA": 0.98,
        "APAC": 0.94,
    }[region]
    device_factor = {"Desktop": 1.06, "Mobile": 0.96}[device_type]
    browser_factor = {"Chrome": 1.02, "Safari": 0.97, "Firefox": 0.99}[browser]
    channel_factor = {"Organic": 1.00, "Paid Search": 1.12, "Email": 0.86}[channel]
    segment_factor = {"SMB": 0.88, "Mid-Market": 1.00, "Enterprise": 1.22}[business_segment]

    impressions = int(
        850
        * region_factor
        * device_factor
        * channel_factor
        * segment_factor
        * (1 + 0.06 * weekly)
        + rng.normal(0, 35)
    )
    impressions = max(impressions, 250)

    click_through_rate = (
        0.078
        * channel_factor
        * browser_factor
        * (1 + 0.015 * weekly)
        + rng.normal(0, 0.002)
    )
    click_through_rate = float(np.clip(click_through_rate, 0.015, 0.18))
    clicks = int(round(impressions * click_through_rate))

    conversion_rate = (
        0.092
        * region_factor
        * device_factor
        * browser_factor
        * segment_factor
        * (1 + trend)
        + rng.normal(0, 0.003)
    )
    conversion_rate = float(np.clip(conversion_rate, 0.015, 0.25))
    conversions = int(round(clicks * conversion_rate))
    orders = max(0, int(round(conversions * (0.78 + rng.normal(0, 0.025)))))

    average_order_value = (
        72
        * segment_factor
        * {"Organic": 0.98, "Paid Search": 1.06, "Email": 0.94}[channel]
        * (1 + 0.02 * weekly)
        + rng.normal(0, 2.6)
    )
    average_order_value = float(np.clip(average_order_value, 20, 220))
    revenue = orders * average_order_value

    latency_ms = (
        205
        * {"North America": 0.92, "EMEA": 1.03, "APAC": 1.12}[region]
        * {"Desktop": 0.9, "Mobile": 1.12}[device_type]
        * {"Chrome": 0.94, "Safari": 1.02, "Firefox": 1.06}[browser]
        + rng.normal(0, 8)
    )
    latency_ms = float(np.clip(latency_ms, 60, 900))

    return {
        "impressions": impressions,
        "clicks": clicks,
        "conversions": conversions,
        "orders": orders,
        "revenue": revenue,
        "latency_ms": latency_ms,
        "conversion_rate": conversions / clicks if clicks else 0.0,
        "click_through_rate": clicks / impressions if impressions else 0.0,
        "average_order_value": revenue / orders if orders else 0.0,
        "revenue_per_session": revenue / impressions if impressions else 0.0,
    }


def generate_kpi_data(
    output_path: Path = DEFAULT_OUTPUT_PATH,
    seed: int = DEFAULT_SEED,
    end_date: str = DEFAULT_END_DATE,
    days: int = DEFAULT_DAYS,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    end_timestamp = pd.Timestamp(end_date)
    dates = pd.date_range(end=end_timestamp, periods=days, freq="D")
    rows = []

    for date_index, date in enumerate(dates):
        for region in REGIONS:
            for device_type in DEVICE_TYPES:
                for browser in BROWSERS:
                    for channel in CHANNELS:
                        for business_segment in BUSINESS_SEGMENTS:
                            metrics = _base_metrics(
                                rng,
                                date_index,
                                region,
                                device_type,
                                browser,
                                channel,
                                business_segment,
                            )

                            for kpi_name in KPI_NAMES:
                                adjusted_metrics = metrics.copy()
                                incident = _incident_for_row(
                                    date,
                                    kpi_name,
                                    region,
                                    device_type,
                                    browser,
                                    channel,
                                    business_segment,
                                    end_timestamp,
                                )

                                if incident["is_incident"] and kpi_name == "conversion_rate":
                                    adjusted_metrics["conversions"] = int(
                                        round(adjusted_metrics["conversions"] * 0.55)
                                    )
                                    adjusted_metrics["orders"] = int(
                                        round(adjusted_metrics["orders"] * 0.55)
                                    )
                                    adjusted_metrics["revenue"] = (
                                        adjusted_metrics["orders"]
                                        * adjusted_metrics["average_order_value"]
                                    )
                                    adjusted_metrics["conversion_rate"] = (
                                        adjusted_metrics["conversions"] / adjusted_metrics["clicks"]
                                        if adjusted_metrics["clicks"]
                                        else 0.0
                                    )

                                if incident["is_incident"] and kpi_name == "latency_ms":
                                    adjusted_metrics["latency_ms"] = min(
                                        adjusted_metrics["latency_ms"] + 185,
                                        900,
                                    )

                                if incident["is_incident"] and kpi_name == "revenue_per_session":
                                    adjusted_metrics["revenue"] *= 0.62
                                    adjusted_metrics["revenue_per_session"] = (
                                        adjusted_metrics["revenue"] / adjusted_metrics["impressions"]
                                        if adjusted_metrics["impressions"]
                                        else 0.0
                                    )

                                kpi_value = adjusted_metrics[kpi_name]
                                rows.append({
                                    "date": date.strftime("%Y-%m-%d"),
                                    "kpi_name": kpi_name,
                                    "region": region,
                                    "device_type": device_type,
                                    "browser": browser,
                                    "channel": channel,
                                    "business_segment": business_segment,
                                    "impressions": int(adjusted_metrics["impressions"]),
                                    "clicks": int(adjusted_metrics["clicks"]),
                                    "conversions": int(adjusted_metrics["conversions"]),
                                    "orders": int(adjusted_metrics["orders"]),
                                    "revenue": round(float(adjusted_metrics["revenue"]), 2),
                                    "latency_ms": round(float(adjusted_metrics["latency_ms"]), 2),
                                    "kpi_value": round(float(kpi_value), 6),
                                    **incident,
                                })

    df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic raw KPI data.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    args = parser.parse_args()

    df = generate_kpi_data(
        output_path=Path(args.output),
        seed=args.seed,
        end_date=args.end_date,
        days=args.days,
    )
    print(f"Generated {len(df):,} rows at {args.output}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Incident rows: {int(df['is_incident'].sum()):,}")


if __name__ == "__main__":
    main()
