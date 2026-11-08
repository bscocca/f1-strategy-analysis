{{ config(severity='warn') }}

-- Stints of the same driver in the same race should have a valid lap range
-- (lap_start <= lap_end) and should not share any lap.
-- The source has a few known violations, handled in fct_laps by keeping the
-- most recent stint: this test lists them as a warning to monitor their number.

with stints as (

    select * from {{ ref('stg_openf1__stints') }}

),

invalid_ranges as (

    select
        stint_id,
        null as overlapping_stint_id,
        'lap_end before lap_start' as problem
    from stints
    where lap_end < lap_start

),

overlapping_stints as (

    select
        a.stint_id,
        b.stint_id as overlapping_stint_id,
        'overlapping laps' as problem
    from stints as a
    inner join stints as b
        on a.session_key = b.session_key
        and a.driver_number = b.driver_number
        and a.stint_number < b.stint_number
        and a.lap_start <= b.lap_end
        and b.lap_start <= a.lap_end
    where a.lap_start <= a.lap_end
      and b.lap_start <= b.lap_end

)

select * from invalid_ranges
union all
select * from overlapping_stints