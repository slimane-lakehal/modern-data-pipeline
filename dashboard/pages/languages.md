---
title: Language Trends
---

# Language Trends 🐍

_Which programming languages dominate the data-engineering open source ecosystem?_

```sql language_overview
select
    language,
    repo_count,
    avg_language_pct,
    star_weighted_pct,
    total_stars_in_repos,
    avg_stars_per_repo,
    top_repos_count,
    rank_by_repos
from marts.mart_language_trends
where rank_by_repos <= 20
order by repo_count desc
```

## Top Languages by Repo Count

<BarChart
  data={language_overview}
  x="language"
  y="repo_count"
  title="Number of repos using each language"
  colorPalette={['#6366f1']}
/>

---

## Language Popularity vs Star Weight

> _Star-weighted % = how dominant a language is, weighted by repo popularity_

<ScatterPlot
  data={language_overview}
  x="repo_count"
  y="star_weighted_pct"
  series="language"
  title="Repo count vs Star-weighted dominance"
  xAxisTitle="Repos using language"
  yAxisTitle="Star-weighted % share"
/>

---

## Full Language Table

<DataTable data={language_overview} rows=20>
  <Column id="rank_by_repos" title="#" />
  <Column id="language" title="Language" />
  <Column id="repo_count" title="Repos" />
  <Column id="avg_language_pct" title="Avg % in repo" fmt="num1" />
  <Column id="star_weighted_pct" title="Star-weighted %" fmt="num1" />
  <Column id="avg_stars_per_repo" title="Avg stars" fmt="num0" />
  <Column id="top_repos_count" title="Top repos" />
</DataTable>
