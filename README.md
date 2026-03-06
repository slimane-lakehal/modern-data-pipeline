# Modern Data Pipeline

> End-to-end ELT pipeline tracking **GitHub trending repositories** across the data-engineering ecosystem. Built with **Python + Prefect + dbt + DuckDB + Evidence.dev**.

---

## Problem Statement

Open-source trends move fast. This pipeline automatically tracks which repos, languages, and topics are gaining traction in the data ecosystem — giving an analyst a daily, queryable, dashboarded view of the GitHub landscape.

---

## Architecture

```
┌─────────────────┐
│   GitHub API    │  ← REST API, no scraping
└────────┬────────┘
         │ extract.py (repos + languages)
         ▼
┌─────────────────┐
│  DuckDB (raw)   │  ← Append-only snapshots
│  raw.repos      │
│  raw.languages  │
└────────┬────────┘
         │ dbt build
         ▼
┌─────────────────────────────┐
│  DuckDB (marts)             │
│  staging.stg_repos          │
│  marts.mart_trending_repos  │
│  marts.mart_language_trends │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│  Evidence.dev   │     │  Prefect Cloud   │
│  Dashboard      │     │  Daily schedule  │
└─────────────────┘     └──────────────────┘
```

---

## Quick Start

```bash
# 1. Clone & setup
git clone https://github.com/slimane-lakehal/modern-data-pipeline.git
cd modern-data-pipeline
make setup

# 2. Configure
cp .env.example .env
# → Add your GITHUB_TOKEN (free, read-only)
# → Get one at: https://github.com/settings/tokens

# 3. Run the full pipeline
make run

# 4. View the dashboard
make dashboard   # → http://localhost:3000
```

---

## Dashboard Preview

Three pages powered by Evidence.dev (SQL-first BI):

| Page | Content |
|------|---------|
| **Home** | KPIs — total repos, stars, last update |
| **Trending** | Filterable repo table by topic, stars scatter plot |
| **Languages** | Language popularity, star-weighted rankings |

---

## Tech Stack

| Layer | Tool | Why |
|-------|------|-----|
| **Extract** | Python + `requests` | GitHub REST API, zero dependencies |
| **Storage** | DuckDB | In-process OLAP, fast analytics, zero infra |
| **Transform** | dbt Core | SQL-first, tested, documented models |
| **Orchestrate** | Prefect 2 | Clean Python-native flows, great UI |
| **Visualize** | Evidence.dev | SQL in Markdown, git-native BI |
| **CI/CD** | GitHub Actions | Daily scheduled run |

---

## Project Structure

```
modern-data-pipeline/
├── pipeline/
│   ├── extract.py        # GitHub API client (repos + languages)
│   ├── load.py           # DuckDB loader (idempotent, append-only)
│   └── flows.py          # Prefect flow definitions
├── transform/
│   └── dbt_pipeline/
│       └── models/
│           ├── staging/  # stg_repos, stg_languages
│           └── marts/    # mart_trending_repos, mart_language_trends
├── dashboard/
│   └── pages/
│       ├── index.md      # KPIs + overview
│       ├── trending.md   # Repo explorer
│       └── languages.md  # Language analysis
├── scripts/
│   └── run_extract.py    # Standalone extract (no Prefect)
├── .github/workflows/
│   └── pipeline-ci.yml   # Daily CI + manual trigger
├── Makefile
├── requirements.txt
└── .env.example
```

---

## Key Design Decisions

**Append-only raw tables** — Each daily run appends a new snapshot. This allows time-series analysis (how have stars grown? which repos went viral?) without needing a data warehouse.

**Idempotent loads** — Re-running the pipeline on the same day deletes today's rows before re-inserting. Safe to retry.

**dbt `ephemeral` → `table`** — Raw data is append-only; dbt staging models deduplicate to the latest snapshot, so marts always see clean, current data.

**Evidence.dev over Metabase/Superset** — SQL embedded in Markdown = git-versioned dashboards, zero database connection config for viewers, deploys as a static site.

---

## Scheduling with Prefect

```bash
# Deploy as a daily flow
prefect deployment build pipeline/flows.py:run_pipeline \
    --name github-daily \
    --cron "0 8 * * *" \
    --apply
```

---

## Author

**Slimane** — Data Analyst & Analytics Engineer  
Instructor @ Le Wagon · Founder @ AuditGuard AI · LIFO.AI

[LinkedIn](https://linkedin.com/in/lakehal-slimane) · [Portfolio](https://slimane-lakehal.github.io/portfolio/) · [GitHub](https://github.com/slimane-lakehal)
