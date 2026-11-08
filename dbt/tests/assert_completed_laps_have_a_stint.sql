-- Every completed lap (with a lap time) must fall within one of the
-- driver's stints, otherwise it has no tyre information.
-- Returns the laps that break this rule.

select
    lap_id,
    season,
    circuit_name,
    driver_code,
    lap_number,
    lap_time_s
from {{ ref('fct_laps') }}
where lap_time_s is not null
  and stint_number is null