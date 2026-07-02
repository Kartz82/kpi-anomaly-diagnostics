# Interview Notes

## Why anomaly detection?

It separates normal KPI movement from behavior that needs investigation.

## Why rolling Z-score?

It is a simple statistical baseline that is easy to explain and compare against
more advanced detectors.

## Why an ML residual detector?

It can learn expected KPI behavior from time and dimension context, which helps
catch patterns the statistical baseline misses.

## Why not simple thresholds only?

Static thresholds ignore seasonality, segment behavior, and context. They are
too blunt for portfolio-grade diagnostics.

## How does RCA work?

The RCA step measures degradation contribution by dimension and dimension
combination, then ranks the largest contributors for each KPI/date pair.

## How does this help executives?

It turns metric movement into an action-oriented summary that names the KPI,
the severity, the likely driver, and the next step.

## Why dbt?

dbt turns the verified warehouse into tested, documented marts that are easier
to explain in interviews and easier to reuse later.

## How would this be productionized?

Add real source ingestion, schedule the pipeline, deploy the dashboard, wire in
alerts, and host dbt docs and warehouse artifacts in a stable environment.
