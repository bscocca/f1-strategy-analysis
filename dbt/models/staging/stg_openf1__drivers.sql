with source as (

    select * from {{ source('openf1', 'raw_drivers') }}

),

renamed as (

    select
        -- Surrogate key: one row per race and driver.
        -- Driver numbers can change between seasons, so a driver number
        -- identifies a driver only within a race
        concat_ws('-', session_key, driver_number) as race_driver_id,

        cast(session_key as integer) as session_key,
        cast(meeting_key as integer) as meeting_key,
        cast(driver_number as integer) as driver_number,

        name_acronym as driver_code,
        -- "Max Verstappen" instead of the API's "Max VERSTAPPEN", for charts
        concat_ws(' ', first_name, last_name) as driver_name,

        team_name,
        -- Hex colour with the leading # expected by plotting libraries
        '#' || team_colour as team_colour

        -- broadcast_name, full_name, headshot_url and country_code are not used and are dropped

    from source

)

select * from renamed