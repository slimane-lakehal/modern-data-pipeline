-- mart_trending_repos.sql
-- Top repos enriched with language details.
-- Ready for Evidence.dev dashboarding.

with repos as (
    select * from {{ ref('stg_repos') }}
),

-- Language diversity per repo (count of languages used)
lang_diversity as (
    select
        repo_id,
        count(distinct language)            as language_count,
        -- Top 3 languages as a readable string: "Python, SQL, Shell"
        string_agg(language, ', ' order by language_pct desc) as languages_used
    from {{ ref('stg_languages') }}
    group by repo_id
),

final as (
    select
        r.repo_id,
        r.repo_name,
        r.full_name,
        r.owner_login,
        r.owner_type,
        r.description,
        r.primary_language,
        r.stars,
        r.forks,
        r.open_issues,
        r.watchers,
        r.topics,
        r.license,
        r.html_url,
        r.source_topic,
        r.created_at,
        r.last_pushed_at,
        r.snapshot_at,
        r.repo_age_days,
        r.popularity_tier,

        -- Language enrichment
        coalesce(l.language_count, 0)       as language_count,
        l.languages_used,

        -- Engagement ratio
        round(1.0 * r.forks / nullif(r.stars, 0), 4) as fork_to_star_ratio,

        -- Stars per day since creation (velocity)
        round(1.0 * r.stars / nullif(r.repo_age_days, 0), 2) as stars_per_day

    from repos r
    left join lang_diversity l on r.repo_id = l.repo_id
)

select * from final
order by stars desc
