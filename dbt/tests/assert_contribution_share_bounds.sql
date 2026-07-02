select *
from {{ ref('fact_rca_contributions') }}
where contribution_share < 0 or contribution_share > 1

