---
title: GitHub Trends Dashboard
---

# GitHub Ecosystem Trends 🐙

_Tracking trending repositories across the data-engineering ecosystem — updated daily via a Prefect + dbt pipeline._

```sql summary_stats
select
    count(distinct repo_id)     as total_repos,
    count(distinct owner_login) as unique_owners,
    sum(stars)                  as total_stars,
    max(snapshot_at)::date      as last_updated
from marts.mart_trending_repos
```

<BigValue
  data={summary_stats}
  value="total_repos"
  title="Repos tracked"
/>
<BigValue
  data={summary_stats}
  value="total_stars"
  title="Total stars"
  fmt="num0"
/>
<BigValue
  data={summary_stats}
  value="unique_owners"
  title="Unique authors"
/>
<BigValue
  data={summary_stats}
  value="last_updated"
  title="Last updated"
/>

---

## 🏆 Top 10 Repos by Stars

```sql top_repos
select
    repo_name,
    owner_login,
    primary_language,
    stars,
    forks,
    stars_per_day,
    popularity_tier,
    html_url
from marts.mart_trending_repos
order by stars desc
limit 10
```

<DataTable
  data={top_repos}
  link="html_url"
  rows=10
>
  <Column id="repo_name" title="Repo" />
  <Column id="owner_login" title="Owner" />
  <Column id="primary_language" title="Language" />
  <Column id="stars" title="⭐ Stars" fmt="num0" />
  <Column id="forks" title="🍴 Forks" fmt="num0" />
  <Column id="stars_per_day" title="Stars/day" fmt="num2" />
  <Column id="popularity_tier" title="Tier" />
</DataTable>

---

## 📊 Stars Distribution by Popularity Tier

```sql tier_distribution
select
    popularity_tier,
    count(*)    as repo_count,
    sum(stars)  as total_stars,
    avg(stars)  as avg_stars
from marts.mart_trending_repos
group by popularity_tier
order by total_stars desc
```

<BarChart
  data={tier_distribution}
  x="popularity_tier"
  y="repo_count"
  title="Repos by Popularity Tier"
  colorPalette={['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd']}
/>
