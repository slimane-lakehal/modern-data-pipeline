-- stg_repos.sql
-- Latest snapshot only — deduplicates the append-only raw table
-- so marts always work on the most recent data per repo.

with source as (
    select * from {{ source('raw', 'repos') }}
),

-- Keep only the latest snapshot for each repo
latest as (
    select *,
        row_number() over (
            partition by repo_id
            order by snapshot_at desc
        ) as rn
    from source
),

renamed as (
    select
        repo_id,
        name                                    as repo_name,
        full_name,
        owner_login,
        owner_type,
        description,
        primary_language,
        stars,
        forks,
        open_issues,
        watchers,
        is_fork,
        is_archived,
        cast(created_at as timestamp)           as created_at,
        cast(pushed_at  as timestamp)           as last_pushed_at,
        topics,
        license,
        html_url,
        source_topic,
        cast(snapshot_at as timestamp)          as snapshot_at,

        -- derived
        datediff('day', cast(created_at as timestamp), current_date) as repo_age_days,

        case
            when stars >= 10000 then 'very-popular'
            when stars >= 1000  then 'popular'
            when stars >= 100   then 'growing'
            else 'niche'
        end as popularity_tier

    from latest
    where rn = 1
      and is_archived = false   -- exclude archived repos
)

select * from renamed
