with source as (

    select * from {{ source('openf1', 'raw_pit') }}

),

renamed as (

    select
        -- Surrogate key: one row per race, driver and lap of pit entry
        concat_ws('-', session_key, driver_number, lap_number) as pit_stop_id,

        cast(session_key as integer) as session_key,
        cast(meeting_key as integer) as meeting_key,
        cast(driver_number as integer) as driver_number,
        -- The lap on which the driver entered the pit lane (in-lap)
        cast(lap_number as integer) as lap_number,
        {{ to_utc_timestamp('date') }} as pit_entered_at,

        -- lane_duration replaced pit_duration (removed at the end of 2026):
        -- older records may only have the old name
        cast(coalesce(lane_duration, pit_duration) as double) as pit_lane_time_s,

        -- Stationary time, available only from the 2024 US Grand Prix onwards
        cast(stop_duration as double) as stop_time_s

    from source

)

select * from renamed