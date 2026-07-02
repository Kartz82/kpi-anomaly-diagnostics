from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import streamlit as st

try:
    import plotly.express as px
except Exception:  # pragma: no cover - graceful fallback if plotly is unavailable
    px = None


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = DATA_DIR / "reports"

# Dashboard reads local CSV and JSON outputs by default from:
# data/processed/kpi_monitoring_table.csv
# data/processed/anomaly_results.csv
# data/processed/rca_contribution_table.csv
# data/reports/data_quality_report.json
# data/reports/kpi_monitoring_summary.json
# data/reports/model_evaluation.csv
# data/reports/model_comparison.json
# data/reports/root_cause_summary.json
# data/reports/latest_incident.json
# data/reports/incident_history.csv
MONITORING_PATH = PROCESSED_DIR / "kpi_monitoring_table.csv"
ANOMALY_PATH = PROCESSED_DIR / "anomaly_results.csv"
RCA_PATH = PROCESSED_DIR / "rca_contribution_table.csv"
DQ_PATH = REPORTS_DIR / "data_quality_report.json"
MONITORING_SUMMARY_PATH = REPORTS_DIR / "kpi_monitoring_summary.json"
MODEL_EVAL_PATH = REPORTS_DIR / "model_evaluation.csv"
MODEL_COMPARISON_PATH = REPORTS_DIR / "model_comparison.json"
RCA_SUMMARY_PATH = REPORTS_DIR / "root_cause_summary.json"
LATEST_INCIDENT_PATH = REPORTS_DIR / "latest_incident.json"
INCIDENT_HISTORY_PATH = REPORTS_DIR / "incident_history.csv"

PAGES = [
    "Executive Overview",
    "KPI Health",
    "Anomaly Timeline",
    "Root Cause Explorer",
    "Data Quality",
    "Incident Center",
]

DIMENSION_COLUMNS = ["region", "device_type", "browser", "channel", "business_segment"]


def _safe_read_csv(path: Path, parse_dates: Iterable[str] | None = None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    kwargs: dict[str, Any] = {"low_memory": False}
    if parse_dates:
        kwargs["parse_dates"] = list(parse_dates)
    return pd.read_csv(path, **kwargs)


@st.cache_data(show_spinner=False)
def load_monitoring() -> pd.DataFrame:
    return _safe_read_csv(MONITORING_PATH, parse_dates=["date"])


@st.cache_data(show_spinner=False)
def load_anomalies() -> pd.DataFrame:
    return _safe_read_csv(ANOMALY_PATH, parse_dates=["date"])


@st.cache_data(show_spinner=False)
def load_rca() -> pd.DataFrame:
    return _safe_read_csv(RCA_PATH, parse_dates=["analysis_date"])


@st.cache_data(show_spinner=False)
def load_incident_history() -> pd.DataFrame:
    return _safe_read_csv(INCIDENT_HISTORY_PATH, parse_dates=["date"])


@st.cache_data(show_spinner=False)
def load_model_eval() -> pd.DataFrame:
    return _safe_read_csv(MODEL_EVAL_PATH)


@st.cache_data(show_spinner=False)
def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path) as handle:
        return json.load(handle)


def _make_figure(data: pd.DataFrame, kind: str, x: str, y: str, color: str | None = None, title: str = ""):
    if data.empty:
        return None
    if px is None:
        if kind == "line":
            return data.set_index(x)[[y]].sort_index()
        if kind == "bar":
            return data.set_index(x)[[y]]
        return None
    if kind == "line":
        return px.line(data, x=x, y=y, color=color, title=title)
    if kind == "bar":
        return px.bar(data, x=x, y=y, color=color, title=title)
    if kind == "area":
        return px.area(data, x=x, y=y, color=color, title=title)
    return None


def _display_figure(fig) -> None:
    if fig is None:
        st.info("No data available for this view.")
    elif hasattr(fig, "data"):
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.dataframe(fig, use_container_width=True)


def _load_core_context() -> dict[str, Any]:
    return {
        "monitoring": load_monitoring(),
        "anomalies": load_anomalies(),
        "rca": load_rca(),
        "incident_history": load_incident_history(),
        "model_eval": load_model_eval(),
        "dq": load_json(DQ_PATH),
        "monitoring_summary": load_json(MONITORING_SUMMARY_PATH),
        "model_comparison": load_json(MODEL_COMPARISON_PATH),
        "rca_summary": load_json(RCA_SUMMARY_PATH),
        "latest_incident": load_json(LATEST_INCIDENT_PATH),
    }


def _format_percent(value: Any) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except Exception:
        return "n/a"


def render_executive_overview(ctx: dict[str, Any]) -> None:
    monitoring = ctx["monitoring"]
    anomalies = ctx["anomalies"]
    dq = ctx["dq"]
    model_comparison = ctx["model_comparison"]
    monitoring_summary = ctx["monitoring_summary"]
    latest_incident = ctx["latest_incident"]
    incidents = latest_incident.get("incidents", [])

    st.subheader("Executive Overview")
    if monitoring.empty or anomalies.empty:
        st.warning("Required local data files are missing.")
        return

    kpi_count = monitoring["kpi_name"].nunique()
    date_min = monitoring["date"].min()
    date_max = monitoring["date"].max()
    health_score = dq.get("health_score", 0)
    anomaly_count = int(anomalies["combined_anomaly"].sum()) if "combined_anomaly" in anomalies else 0
    incident_count = len(incidents)
    highest_severity = latest_incident.get("highest_severity", "n/a")
    best_detector = model_comparison.get("best_detector", "n/a")
    best_detector_f1 = model_comparison.get("best_detector_f1_score", "n/a")

    cards = st.columns(6)
    cards[0].metric("KPIs Monitored", f"{kpi_count}")
    date_range_label = f"{date_min:%Y-%m-%d} to {date_max:%Y-%m-%d}" if hasattr(date_min, "strftime") else f"{date_min} to {date_max}"
    cards[1].metric("Date Range", date_range_label)
    cards[2].metric("Data Health", f"{health_score}")
    cards[3].metric("Anomalies", f"{anomaly_count:,}")
    cards[4].metric("Incidents", f"{incident_count}")
    cards[5].metric("Best Detector", f"{best_detector} ({best_detector_f1})")

    st.markdown("### KPI Health Summary")
    health = monitoring.groupby("kpi_name", as_index=False).agg(
        threshold_breaches=("threshold_breached", "sum"),
        avg_variance=("percent_variance", "mean"),
        max_variance=("percent_variance", lambda s: s.abs().max()),
    )
    st.dataframe(health.sort_values("threshold_breaches", ascending=False), use_container_width=True)

    st.markdown("### Latest / Top Incident")
    if incidents:
        incident = latest_incident.get("highest_confidence_incident") or incidents[0]
        st.write(incident.get("executive_summary", "No executive summary available."))
        st.caption(f"Severity: {incident.get('severity', 'n/a')} | Confidence: {incident.get('confidence_label', 'n/a')}")
    else:
        st.info("No incidents available.")

    st.markdown("### Monitoring Summary")
    summary_table = pd.DataFrame(
        [
            {
                "warning_count": monitoring_summary.get("warning_count"),
                "critical_count": monitoring_summary.get("critical_count"),
                "threshold_breach_count": monitoring_summary.get("threshold_breach_count"),
                "highest_severity": highest_severity,
            }
        ]
    )
    st.dataframe(summary_table, use_container_width=True)


def render_kpi_health(ctx: dict[str, Any]) -> None:
    monitoring = ctx["monitoring"]
    st.subheader("KPI Health")
    if monitoring.empty:
        st.warning("Monitoring data not available.")
        return

    kpi = st.sidebar.selectbox("KPI", sorted(monitoring["kpi_name"].dropna().unique()))
    date_min = pd.to_datetime(monitoring["date"]).min()
    date_max = pd.to_datetime(monitoring["date"]).max()
    date_range = st.sidebar.slider(
        "Date Range",
        min_value=date_min.to_pydatetime(),
        max_value=date_max.to_pydatetime(),
        value=(date_min.to_pydatetime(), date_max.to_pydatetime()),
    )

    filtered = monitoring[monitoring["kpi_name"] == kpi].copy()
    filtered["date"] = pd.to_datetime(filtered["date"])
    filtered = filtered[(filtered["date"] >= pd.Timestamp(date_range[0])) & (filtered["date"] <= pd.Timestamp(date_range[1]))]

    for column in DIMENSION_COLUMNS:
        options = sorted(filtered[column].dropna().unique()) if not filtered.empty else []
        selected = st.sidebar.multiselect(f"{column.title()} filter", options, default=options[:1] if options else [])
        if selected:
            filtered = filtered[filtered[column].isin(selected)]

    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", f"{len(filtered):,}")
    c2.metric("Threshold Breaches", f"{int(filtered['threshold_breached'].sum()) if 'threshold_breached' in filtered else 0:,}")
    c3.metric("Monitoring Statuses", f"{filtered['monitoring_status'].nunique() if 'monitoring_status' in filtered else 0}")

    chart_df = filtered.sort_values("date")
    fig = None
    if not chart_df.empty and px is not None:
        melted = chart_df.melt(
            id_vars=["date"],
            value_vars=["actual_value", "expected_value", "moving_baseline"],
            var_name="series",
            value_name="value",
        )
        fig = px.line(melted, x="date", y="value", color="series", title=f"{kpi} actual vs expected")
    elif not chart_df.empty:
        fig = chart_df.set_index("date")[["actual_value", "expected_value", "moving_baseline"]]
    _display_figure(fig)

    st.markdown("### Monitoring Status Distribution")
    status_counts = filtered.groupby("monitoring_status", as_index=False).size().rename(columns={"size": "rows"})
    st.dataframe(status_counts, use_container_width=True)

    st.markdown("### Threshold Breaches by KPI")
    breach_counts = monitoring.groupby("kpi_name", as_index=False)["threshold_breached"].sum().sort_values("threshold_breached", ascending=False)
    breach_fig = _make_figure(breach_counts, "bar", "kpi_name", "threshold_breached", title="Threshold breaches by KPI")
    _display_figure(breach_fig)

    st.markdown("### Worst Percent Variances")
    worst = filtered.assign(abs_percent_variance=filtered["percent_variance"].abs()).sort_values("abs_percent_variance", ascending=False)
    st.dataframe(
        worst[[
            "date",
            "region",
            "device_type",
            "browser",
            "channel",
            "business_segment",
            "actual_value",
            "expected_value",
            "percent_variance",
            "monitoring_status",
        ]].head(20),
        use_container_width=True,
    )


def render_anomaly_timeline(ctx: dict[str, Any]) -> None:
    anomalies = ctx["anomalies"]
    model_eval = ctx["model_eval"]
    st.subheader("Anomaly Timeline")
    if anomalies.empty:
        st.warning("Anomaly data not available.")
        return

    detector_options = ["residual_anomaly", "zscore_anomaly", "combined_anomaly", "threshold_breached"]
    detector = st.sidebar.selectbox("Detector", detector_options)
    subset = anomalies[anomalies[detector] == True].copy()  # noqa: E712
    subset["date"] = pd.to_datetime(subset["date"])

    counts = subset.groupby("date", as_index=False).size().rename(columns={"size": "anomalies"})
    _display_figure(_make_figure(counts, "line", "date", "anomalies", title="Anomalies over time"))

    severity = subset.groupby("combined_severity", as_index=False).size().rename(columns={"size": "rows"})
    st.dataframe(severity, use_container_width=True)

    st.markdown("### Model Evaluation")
    if model_eval.empty:
        st.info("Model evaluation not available.")
    else:
        st.dataframe(model_eval, use_container_width=True)
        best_row = model_eval.sort_values("f1_score", ascending=False).iloc[0]
        st.success(f"Best detector by F1: {best_row['detector']} ({best_row['f1_score']:.3f})")


def render_root_cause_explorer(ctx: dict[str, Any]) -> None:
    rca = ctx["rca"]
    summary = ctx["rca_summary"]
    st.subheader("Root Cause Explorer")
    if rca.empty:
        st.warning("RCA data not available.")
        return

    kpi = st.sidebar.selectbox("RCA KPI", sorted(rca["kpi_name"].dropna().unique()), key="rca_kpi")
    date = st.sidebar.selectbox("RCA Date", sorted(rca["analysis_date"].dropna().astype(str).unique()), key="rca_date")
    dimension_type = st.sidebar.selectbox(
        "Dimension Type",
        ["region", "device_type", "browser", "channel", "business_segment", "region_device_browser", "full_segment"],
        key="rca_dim",
    )
    detector = st.sidebar.selectbox(
        "Detector",
        sorted(rca["detector_used"].dropna().unique()),
        index=0,
        key="rca_detector",
    )

    filtered = rca[
        (rca["kpi_name"] == kpi)
        & (rca["analysis_date"].astype(str) == date)
        & (rca["dimension_type"] == dimension_type)
        & (rca["detector_used"] == detector)
    ].copy()
    filtered = filtered.sort_values(["contribution_share", "degradation_amount"], ascending=False)

    st.markdown("### Top Contributors")
    _display_figure(_make_figure(filtered.head(10), "bar", "dimension_value", "contribution_share", title="Top RCA contributors"))

    st.dataframe(
        filtered[[
            "analysis_date",
            "kpi_name",
            "dimension_type",
            "dimension_value",
            "actual_value_sum_or_avg",
            "expected_value_sum_or_avg",
            "degradation_amount",
            "contribution_share",
            "contribution_rank",
            "severity_max",
            "recommended_action",
        ]].head(20),
        use_container_width=True,
    )

    st.markdown("### Root Cause Statements")
    statements = summary.get("top_root_cause_statements", [])
    for statement in statements[:5]:
        st.write(f"- {statement}")

    if not filtered.empty:
        top = filtered.iloc[0]
        st.info(
            f"Example: {kpi} on {date} - {top['dimension_value']} contributed "
            f"{top['contribution_share'] * 100:.1f}% of measured degradation."
        )


def render_data_quality(ctx: dict[str, Any]) -> None:
    dq = ctx["dq"]
    st.subheader("Data Quality")
    if not dq:
        st.warning("Data quality report not available.")
        return

    checks = dq.get("checks", {})
    st.metric("Overall Health Score", dq.get("health_score", "n/a"))
    st.metric("Validation Status", dq.get("status", "n/a"))

    summary = pd.DataFrame(
        [
            {
                "schema": checks.get("schema", {}).get("passed"),
                "data_types": checks.get("data_types", {}).get("passed"),
                "accepted_values": checks.get("accepted_values", {}).get("passed"),
                "nulls": checks.get("nulls", {}).get("passed"),
                "duplicates": checks.get("duplicates", {}).get("passed"),
                "freshness": checks.get("freshness", {}).get("passed"),
                "completeness": checks.get("completeness", {}).get("passed"),
                "volume": checks.get("volume", {}).get("passed"),
                "numeric_ranges": checks.get("numeric_ranges", {}).get("passed"),
            }
        ]
    )
    st.dataframe(summary, use_container_width=True)

    st.markdown("### Issue Counts")
    issues = pd.DataFrame(dq.get("issues", []))
    if issues.empty:
        st.info("No data quality issues.")
    else:
        st.dataframe(issues, use_container_width=True)

    with st.expander("Raw JSON details"):
        st.json(dq)


def render_incident_center(ctx: dict[str, Any]) -> None:
    latest_incident = ctx["latest_incident"]
    history = ctx["incident_history"]
    st.subheader("Incident Center")
    if history.empty and not latest_incident:
        st.warning("Incident data not available.")
        return

    rows = history.copy()
    if not rows.empty:
        severity_filter = st.sidebar.multiselect("Severity", sorted(rows["severity"].dropna().unique()), default=sorted(rows["severity"].dropna().unique()))
        confidence_filter = st.sidebar.multiselect(
            "Confidence",
            sorted(rows["confidence_label"].dropna().unique()),
            default=sorted(rows["confidence_label"].dropna().unique()),
        )
        if severity_filter:
            rows = rows[rows["severity"].isin(severity_filter)]
        if confidence_filter:
            rows = rows[rows["confidence_label"].isin(confidence_filter)]

    st.dataframe(rows, use_container_width=True)

    incidents = latest_incident.get("incidents", [])
    if incidents:
        selected_id = st.selectbox("Incident Detail", [incident["incident_id"] for incident in incidents])
        detail = next((incident for incident in incidents if incident["incident_id"] == selected_id), incidents[0])
        st.markdown(f"### {detail.get('kpi_affected', 'Incident')}")
        st.write(detail.get("executive_summary", ""))
        st.write(f"Severity: {detail.get('severity', 'n/a')} | Confidence: {detail.get('confidence_label', 'n/a')} ({detail.get('confidence_score', 'n/a')})")
        st.markdown("**Suspected Dimensions**")
        st.write(detail.get("suspected_dimensions", []))
        st.markdown("**Recommended Actions**")
        st.write(detail.get("recommended_actions", []))
        st.markdown("**Supporting Metrics**")
        st.json(detail.get("supporting_metrics", {}))
    else:
        st.info("No detailed incidents available.")


def main() -> None:
    st.set_page_config(page_title="KPI Reliability & Diagnostic Engine", layout="wide")
    st.title("KPI Reliability & Diagnostic Engine")
    st.caption("Executive dashboard for KPI health, anomalies, RCA, incidents, data quality, and warehouse proof.")

    ctx = _load_core_context()
    page = st.sidebar.radio("Dashboard Section", PAGES, index=0)

    if page == "Executive Overview":
        render_executive_overview(ctx)
    elif page == "KPI Health":
        render_kpi_health(ctx)
    elif page == "Anomaly Timeline":
        render_anomaly_timeline(ctx)
    elif page == "Root Cause Explorer":
        render_root_cause_explorer(ctx)
    elif page == "Data Quality":
        render_data_quality(ctx)
    elif page == "Incident Center":
        render_incident_center(ctx)


if __name__ == "__main__":
    main()
