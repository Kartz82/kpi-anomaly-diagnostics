select *
from {{ ref('fact_incidents') }}
where confidence_score < 0 or confidence_score > 1

