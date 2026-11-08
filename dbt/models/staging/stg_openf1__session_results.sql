with source as (

    select * from {{ source('openf1', 'raw_session_result') }}

),

prepared as (

    select
        *,
        -- gap_to_leader mixes seconds (e.g. 12.3) and lapped gaps (e.g. "+1 LAP"):
        -- read it as text first, then split it into two columns
        cast(gap_to_leader as varchar) as gap_text
    from source

),

renamed as (

    select
        -- Surrogate key: one row per race and driver
        concat_ws('-', session_key, driver_number) as race_driver_id,

        cast(session_key as integer) as session_key,
        cast(meeting_key as integer) as meeting_key,
        cast(driver_number as integer) as driver_number,

        cast(position as integer) as finish_position,
        cast(number_of_laps as integer) as laps_completed,
        cast(duration as double) as race_time_s,

        -- Gap in seconds for drivers on the lead lap, null for lapped drivers
        try_cast(gap_text as double) as gap_to_winner_s,
        -- Laps behind the winner for lapped drivers, null otherwise
        try_cast(nullif(regexp_extract(gap_text, '\+(\d+) LAP', 1), '') as integer) as laps_behind,

        cast(dnf as boolean) as is_dnf,
        cast(dns as boolean) as is_dns,
        cast(dsq as boolean) as is_dsq

    from prepared

)

select * from renamed