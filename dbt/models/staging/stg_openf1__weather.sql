with source as (

    select * from {{ source('openf1', 'raw_weather') }}

),

renamed as (

    select
        -- Surrogate key: one reading per race and timestamp
        concat_ws('-', session_key, date) as weather_reading_id,

        cast(session_key as integer) as session_key,
        cast(meeting_key as integer) as meeting_key,
        cast(date as timestamptz) as measured_at,

        cast(air_temperature as double) as air_temp_c,
        cast(track_temperature as double) as track_temp_c,
        cast(humidity as double) as humidity_pct,
        cast(pressure as double) as pressure_mbar,
        cast(wind_speed as double) as wind_speed_ms,
        cast(wind_direction as integer) as wind_direction_deg,

        -- The API sends rainfall as 0 or 1
        cast(rainfall as integer) > 0 as is_raining

    from source

)

select * from renamed