with

laps as (
    select * from {{ ref('stg_openf1__laps') }}
),

stints as (
    select * from {{ ref('stg_openf1__stints') }}
),

pit_stops as (
    select * from {{ ref('stg_openf1__pit_stops') }}
),

drivers as (
    select * from {{ ref('stg_openf1__drivers') }}
),

sessions as (
    select * from {{ ref('stg_openf1__sessions') }}
),

neutralised_laps as (
    select * from {{ ref('int_neutralised_laps') }}
),

laps_with_tyres as (

    -- A lap belongs to the stint whose lap range contains it
    select
        laps.*,
        stints.stint_number,
        stints.compound,
        stints.tyre_age_at_start + (laps.lap_number - stints.lap_start) as tyre_age_laps
    from laps
    left join stints
        on laps.session_key = stints.session_key
        and laps.driver_number = stints.driver_number
        and laps.lap_number between stints.lap_start and stints.lap_end

    -- The source occasionally has overlapping stints (e.g. the first laps of
    -- the wet 2025 Australian GP): keep the most recent stint so that every
    -- lap appears exactly once. See tests/assert_stints_do_not_overlap.sql
    qualify row_number() over (
        partition by laps.lap_id
        order by stints.stint_number desc nulls last
    ) = 1

),

joined as (

    select
        laps.lap_id,

        -- Race
        laps.session_key,
        sessions.season,
        sessions.circuit_name,
        sessions.race_started_at,

        -- Driver and team
        laps.driver_number,
        drivers.driver_code,
        drivers.driver_name,
        drivers.team_name,
        drivers.team_colour,

        -- Lap
        laps.lap_number,
        laps.lap_started_at,
        laps.lap_time_s,
        laps.sector_1_s,
        laps.sector_2_s,
        laps.sector_3_s,
        laps.speed_trap_kmh,

        -- Tyres
        laps.stint_number,
        laps.compound,
        laps.tyre_age_laps,

        -- Flags to exclude laps that do not reflect race pace
        laps.lap_number = 1 as is_first_lap,
        coalesce(laps.is_pit_out_lap, false) as is_pit_out_lap,
        -- A pit entry lap is recorded in the pit table, or is followed by a
        -- pit exit lap. The pit table alone is not enough: OpenF1 has no pit
        -- stops for the first six races of 2023 and misses some in other races
        pit_stops.pit_stop_id is not null
            or coalesce(
                lead(laps.is_pit_out_lap) over (
                    partition by laps.session_key, laps.driver_number
                    order by laps.lap_number
                ),
                false
            )
            as is_pit_in_lap,
        -- SC, VSC or RED; null when the lap was run under green flag
        neutralised_laps.neutralisation,
        neutralised_laps.neutralised_lap_id is not null as is_neutralised

    from laps_with_tyres as laps
    inner join sessions
        on laps.session_key = sessions.session_key
    left join drivers
        on laps.session_key = drivers.session_key
        and laps.driver_number = drivers.driver_number
    left join pit_stops
        on laps.session_key = pit_stops.session_key
        and laps.driver_number = pit_stops.driver_number
        and laps.lap_number = pit_stops.lap_number
    left join neutralised_laps
        on laps.session_key = neutralised_laps.session_key
        and laps.lap_number = neutralised_laps.lap_number

),

final as (

    select
        *,
        -- A lap that reflects race pace: completed, under green flag,
        -- not the standing start and not affected by a pit stop
        lap_time_s is not null
            and not is_first_lap
            and not is_pit_out_lap
            and not is_pit_in_lap
            and not is_neutralised
            as is_representative_lap
    from joined

)

select * from final