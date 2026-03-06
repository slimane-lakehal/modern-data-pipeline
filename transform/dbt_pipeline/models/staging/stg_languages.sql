-- stg_languages.sql
-- Latest language breakdown per repo.

with source as (
    select * from {{ source('raw', 'repo_languages') }}
),

latest as (
    select *,
        row_number() over (
            partition by repo_id, language
            order by snapshot_at desc
        ) as rn
    from source
),

renamed as (
    select
        repo_id,
        full_name,
        language,
        bytes,
        pct                             as language_pct,
        cast(snapshot_at as timestamp)  as snapshot_at
    from latest
    where rn = 1
)

select * from renamed
