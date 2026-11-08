with source as (

    select * from {{ source('openf1', 'raw_race_control') }}

),

renamed as (

    select
        cast(session_key as integer) as session_key,
        cast(meeting_key as integer) as meeting_key,
        {{ to_utc_timestamp('date') }} as message_at,
        cast(lap_number as integer) as lap_number,

        -- Often null even when the message is about one driver
        -- (e.g. penalties): the car number is then only in the message text
        cast(driver_number as integer) as driver_number,

        category,
        flag,
        scope,
        cast(sector as integer) as sector,
        message

        -- qualifying_phase is always null in races and is dropped

    from source

)

select * from renamed