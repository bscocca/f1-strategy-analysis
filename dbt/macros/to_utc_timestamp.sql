{% macro to_utc_timestamp(column_name) %}
    {#-
        OpenF1 sends timestamps in UTC. DuckDB's JSON reader loads them as
        TIMESTAMP without time zone, and a plain cast to TIMESTAMPTZ would
        interpret them in the local time zone of the machine running dbt.
        This macro states explicitly that they are UTC.
    -#}
    timezone('UTC', cast({{ column_name }} as timestamp))
{% endmacro %}