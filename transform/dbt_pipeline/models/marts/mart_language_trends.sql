-- mart_language_trends.sql
-- Aggregates language popularity across all tracked repos.
-- Answers: "What languages dominate the data-engineering ecosystem?"

with languages as (
    select * from {{ ref('stg_languages') }}
),

repos as (
    select repo_id, stars, popularity_tier, source_topic
    from {{ ref('stg_repos') }}
),

joined as (
    select
        l.language,
        l.language_pct,
        l.bytes,
        r.stars,
        r.popularity_tier,
        r.source_topic
    from languages l
    inner join repos r on l.repo_id = r.repo_id
),

aggregated as (
    select
        language,

        -- How many repos use this language?
        count(*)                            as repo_count,

        -- Average share of this language within repos that use it
        round(avg(language_pct), 2)         as avg_language_pct,

        -- Total bytes across all repos
        sum(bytes)                          as total_bytes,

        -- Weighted by stars (popular repos count more)
        round(sum(language_pct * stars) / nullif(sum(stars), 0), 2) as star_weighted_pct,

        -- Stars of repos using this language
        sum(stars)                          as total_stars_in_repos,
        round(avg(stars), 0)                as avg_stars_per_repo,

        -- How many "very-popular" repos use this language?
        sum(case when popularity_tier = 'very-popular' then 1 else 0 end) as top_repos_count

    from joined
    group by language
    having repo_count >= 3      -- filter noise: only languages in 3+ repos
),

final as (
    select
        *,
        -- Rank by number of repos using the language
        row_number() over (order by repo_count desc)    as rank_by_repos,
        row_number() over (order by avg_language_pct desc) as rank_by_avg_pct

    from aggregated
)

select * from final
order by repo_count desc
