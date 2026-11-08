-- Every driver who finished a race must have exactly one of: gap_to_winner_s (on the lead lap) or laps_behind (lapped).
-- Drivers who retired, did not start or were disqualified have neither.
-- Returns the rows that break this rule: the test passes when there are none.

select *
from {{ ref('stg_openf1__session_results') }}
where
    -- A finisher without any gap: an unrecognised gap format
    (
        gap_to_winner_s is null
        and laps_behind is null
        and not (coalesce(is_dnf, false) or coalesce(is_dns, false) or coalesce(is_dsq, false))
    )
    -- Both gaps set: the two columns are no longer mutually exclusive
    or (gap_to_winner_s is not null and laps_behind is not null)