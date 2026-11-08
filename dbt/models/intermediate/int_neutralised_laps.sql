-- One row per race and leader lap run under safety car, virtual safety car
-- or red flag conditions, derived from race control messages.
--
-- Rules (laps are the race leader's laps, as in race control messages):
--   SC:  from the deployment lap to the "IN THIS LAP" lap, plus the restart lap
--   VSC: from the deployment lap to the ending lap
--   RED: the red flag lap and the restart lap
-- A period without its closing message ends where the next period starts,
-- or at the last lap of the race.
--
-- Red flags are recognised from two signals: a RED flag message and a
-- "SESSION ABORTED" status. Until 2025 they usually appear together; in 2026
-- some red flags are only reported as "SESSION ABORTED" (e.g. Monza 2026).

with

race_control as (
    select * from {{ ref('stg_openf1__race_control') }}
),

laps as (
    select * from {{ ref('stg_openf1__laps') }}
),

race_length as (

    select
        session_key,
        max(lap_number) as last_lap
    from laps
    group by session_key

),

events as (

    select
        session_key,
        message_at,
        lap_number,
        case
            when message = 'SAFETY CAR DEPLOYED' then 'SC'
            when message in ('VIRTUAL SAFETY CAR DEPLOYED', 'VSC DEPLOYED') then 'VSC'
            when flag = 'RED' or message = 'SESSION ABORTED' then 'RED'
        end as start_type,
        case
            when message = 'SAFETY CAR IN THIS LAP' then 'SC'
            when message in ('VIRTUAL SAFETY CAR ENDING', 'VSC ENDING') then 'VSC'
        end as end_type
    from race_control
    where lap_number is not null

),

period_starts as (

    select
        session_key,
        message_at,
        lap_number,
        start_type,
        lead(message_at) over (partition by session_key order by message_at) as next_start_at,
        lead(lap_number) over (partition by session_key order by message_at) as next_start_lap
    from events
    where start_type is not null

),

periods as (

    -- Match each start with the first closing message of the same type
    -- that arrives before the next period starts
    select
        period_starts.session_key,
        period_starts.start_type as neutralisation,
        period_starts.lap_number as first_lap,
        period_starts.next_start_lap,
        min(period_ends.lap_number) as end_lap
    from period_starts
    left join events as period_ends
        on period_ends.session_key = period_starts.session_key
        and period_ends.end_type = period_starts.start_type
        and period_ends.message_at > period_starts.message_at
        and (
            period_starts.next_start_at is null
            or period_ends.message_at < period_starts.next_start_at
        )
    group by all

),

periods_with_last_lap as (

    select
        periods.session_key,
        periods.neutralisation,
        periods.first_lap,
        case
            when periods.neutralisation = 'RED' then periods.first_lap + 1
            when periods.neutralisation = 'SC' and periods.end_lap is not null then periods.end_lap + 1
            when periods.end_lap is not null then periods.end_lap
            else coalesce(periods.next_start_lap, race_length.last_lap)
        end as last_lap
    from periods
    inner join race_length
        on periods.session_key = race_length.session_key

),

laps_in_periods as (

    -- One row per lap covered by each period
    select
        session_key,
        neutralisation,
        unnest(generate_series(first_lap, last_lap)) as lap_number
    from periods_with_last_lap

),

final as (

    -- A lap can fall in more than one period (e.g. a VSC turning into a SC):
    -- keep the most severe neutralisation
    select
        concat_ws('-', session_key, lap_number) as neutralised_lap_id,
        session_key,
        lap_number,
        neutralisation
    from laps_in_periods
    qualify row_number() over (
        partition by session_key, lap_number
        order by
            case neutralisation
                when 'RED' then 1
                when 'SC' then 2
                when 'VSC' then 3
            end
    ) = 1

)

select * from final