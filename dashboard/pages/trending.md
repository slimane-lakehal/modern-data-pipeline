---
title: Trending Repos
---

# Trending Repositories

```sql all_repos
select
    repo_name,
    owner_login,
    owner_type,
    primary_language,
    stars,
    forks,
    open_issues,
    fork_to_star_ratio,
    stars_per_day,
    languages_used,
    language_count,
    popularity_tier,
    source_topic,
    repo_age_days,
    html_url,
    description
from mart_trending_repos
order by stars desc
```

## Filter by Topic

```sql topics
select distinct source_topic as topic
from mart_trending_repos
order by topic
```

<Dropdown
  name="selected_topic"
  data={topics}
  value="topic"
  title="Filter by topic"
  defaultValue="data-engineering"
/>


```sql filtered_repos
select *
from mart_trending_repos
where source_topic = '${inputs.selected_topic.value}'
order by stars desc
limit 50
```

<DataTable data={filtered_repos} link="html_url" rows=15>
  <Column id="repo_name" title="Repository" />
  <Column id="source_topic" title="Topic" />
  <Column id="owner_login" title="Owner" />
  <Column id="primary_language" title="Language" />
  <Column id="stars" title="⭐ Stars" fmt="num0" />
  <Column id="forks" title="Forks" fmt="num0" />
  <Column id="stars_per_day" title="Stars/day" fmt="num2" />
  <Column id="languages_used" title="Languages" />
  <Column id="description" title="Description" />
</DataTable>

---

## Stars vs Forks — Engagement Analysis

```sql engagement
select
    repo_name,
    stars,
    forks,
    fork_to_star_ratio,
    primary_language,
    popularity_tier
from mart_trending_repos
where stars > 500
```

<ScatterPlot
  data={engagement}
  x="stars"
  y="forks"
  series="primary_language"
  title="Stars vs Forks (size = engagement)"
  xAxisTitle="Stars"
  yAxisTitle="Forks"
/>
