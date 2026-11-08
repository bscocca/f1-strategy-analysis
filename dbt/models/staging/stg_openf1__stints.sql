with source as (

    select * from {{ source('openf1', 'raw_stints') }}

),

renamed as (

    select
        -- Surrogate key: one row per race, driver and stint
        concat_ws('-', session_key, driver_number, stint_number) as stint_id,

        cast(session_key as integer) as session_key,
        cast(meeting_key as integer) as meeting_key,
        cast(driver_number as integer) as driver_number,
        cast(stint_number as integer) as stint_number,
        cast(lap_start as integer) as lap_start,
        cast(lap_end as integer) as lap_end,

        -- UNKNOWN means the compound was not recorded: treat it as missing
        nullif(compound, 'UNKNOWN') as compound,

        cast(tyre_age_at_start as integer) as tyre_age_at_start

    from source

)

select * from renamed