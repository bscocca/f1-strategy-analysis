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

final as (

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
        -- The pit table records the lap on which the driver entered the pit lane
        pit_stops.pit_stop_id is not null as is_pit_in_lap

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

)

select * from final