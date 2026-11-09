-- Every pit exit lap must follow a pit entry lap of the same driver.
-- Guards the rule in fct_laps that rebuilds pit entry laps from pit exit
-- laps where the OpenF1 pit table has gaps (e.g. the first races of 2023).
-- Lap 1 is excluded: a driver starting from the pit lane has no lap before.

with laps as (

    select
        session_key,
        circuit_name,
        season,
        driver_code,
        lap_number,
        is_pit_out_lap,
        lag(is_pit_in_lap) over (
            partition by session_key, driver_number
            order by lap_number
        ) as previous_is_pit_in_lap
    from {{ ref('fct_laps') }}

)

select *
from laps
where is_pit_out_lap
    and lap_number > 1
    and not coalesce(previous_is_pit_in_lap, false)