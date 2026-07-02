# Architecture Notes

```mermaid
flowchart LR
    A[Deterministic Raw KPI Generation] --> B[Python Validation / Ingestion]
    B --> C[Processed Analytical Outputs]
    C --> D[KPI Monitoring]
    D --> E[Anomaly Detection and Evaluation]
    E --> F[Contribution-Based RCA]
    F --> G[Incident Reporting]
    C --> H[PostgreSQL Warehouse]
    H --> I[dbt Staging]
    I --> J[dbt Intermediate]
    J --> K[dbt Marts]
    K --> L[Streamlit Dashboard]
    G --> M[Documentation / Proof Artifacts]
    L --> M
    K --> M
```

## Notes

- The Python pipeline produces deterministic raw and processed files first.
- PostgreSQL stores raw, analytics, and marts schemas for warehouse proof.
- dbt adds tested staging, intermediate, and mart layers in separate schemas.
- Streamlit reads the local CSV and JSON artifacts by default for easy demos.
- Documentation and outputs are part of the proof, not an afterthought.
