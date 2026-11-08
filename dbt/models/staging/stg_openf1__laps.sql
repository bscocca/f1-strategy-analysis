with source as (

    select * from {{ source('openf1', 'raw_laps') }}

),

renamed as (

    select
        -- Surrogate key: one row per race, driver and lap
        concat_ws('-', session_key, driver_number, lap_number) as lap_id,

        cast(session_key as integer) as session_key,
        cast(meeting_key as integer) as meeting_key,
        cast(driver_number as integer) as driver_number,
        cast(lap_number as integer) as lap_number,
        cast(date_start as timestamptz) as lap_started_at,

        -- Times in seconds, speeds in km/h
        cast(lap_duration as double) as lap_time_s,
        cast(duration_sector_1 as double) as sector_1_s,
        cast(duration_sector_2 as double) as sector_2_s,
        cast(duration_sector_3 as double) as sector_3_s,
        cast(i1_speed as integer) as speed_i1_kmh,
        cast(i2_speed as integer) as speed_i2_kmh,
        cast(st_speed as integer) as speed_trap_kmh,

        cast(is_pit_out_lap as boolean) as is_pit_out_lap

        -- segments_sector_1/2/3 (mini-sector colours) are not used and are dropped

    from source

)

select * from renamed