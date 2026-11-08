with source as (

    select * from {{ source('openf1', 'raw_sessions') }}

),

renamed as (

    select
        cast(session_key as integer) as session_key,
        cast(meeting_key as integer) as meeting_key,
        cast(year as integer) as season,

        cast(circuit_key as integer) as circuit_key,
        circuit_short_name as circuit_name,
        location,
        country_name,
        country_code,

        {{ to_utc_timestamp('date_start') }} as race_started_at,
        {{ to_utc_timestamp('date_end') }} as race_ended_at,

        coalesce(cast(is_cancelled as boolean), false) as is_cancelled

        -- session_name and session_type are always 'Race' (filtered at download) and are dropped

    from source

)

select * from renamed