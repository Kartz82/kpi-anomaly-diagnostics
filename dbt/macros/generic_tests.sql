{% test unique_combination_of_columns(model, combination_of_columns) %}
select
    {{ combination_of_columns | join(', ') }},
    count(*) as n_records
from {{ model }}
group by {{ combination_of_columns | join(', ') }}
having count(*) > 1
{% endtest %}

{% test assert_contribution_share_bounds(model, column_name) %}
select *
from {{ model }}
where {{ column_name }} < 0 or {{ column_name }} > 1
{% endtest %}

{% test assert_incident_confidence_bounds(model, column_name) %}
select *
from {{ model }}
where {{ column_name }} < 0 or {{ column_name }} > 1
{% endtest %}

