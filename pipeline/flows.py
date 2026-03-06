"""
pipeline/flows.py
-----------------
Prefect flows orchestrating the full ELT pipeline.

Flow structure:
  extract_flow  →  load_flow  →  transform_flow
        └────────────────────────────┘
                 run_pipeline (main)

Run locally:
    python -m pipeline.flows

Schedule (daily at 8am UTC):
    prefect deployment build pipeline/flows.py:run_pipeline \
        --name github-daily \
        --cron "0 8 * * *"
"""

import logging
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash
from datetime import timedelta

from pipeline.extract import fetch_trending_repos, fetch_languages
from pipeline.load import get_connection, init_schema, load_repos, load_languages

load_dotenv()
logging.basicConfig(level=logging.INFO)

DBT_DIR = Path(__file__).parent.parent / "transform" / "dbt_pipeline"
TOPICS = [t.strip() for t in os.getenv("GITHUB_TOPICS", "data-engineering,dbt,python").split(",")]
REPOS_PER_TOPIC = int(os.getenv("REPOS_PER_TOPIC", 50))


# ── Tasks ──────────────────────────────────────────────────────────────────────

@task(
    name="Extract repos from GitHub API",
    retries=2,
    retry_delay_seconds=30,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=12),  # don't re-fetch if run twice same day
)
def extract_repos_task(topics: list[str], per_topic: int) -> list[dict]:
    logger = get_run_logger()
    logger.info(f"Extracting repos for topics: {topics}")
    repos = fetch_trending_repos(topics=topics, per_topic=per_topic)
    logger.info(f"Extracted {len(repos)} repos")
    return repos


@task(
    name="Extract languages from GitHub API",
    retries=2,
    retry_delay_seconds=30,
)
def extract_languages_task(repos: list[dict]) -> list[dict]:
    logger = get_run_logger()
    logger.info(f"Fetching languages for {len(repos)} repos...")
    languages = list(fetch_languages(repos))
    logger.info(f"Extracted {len(languages)} language records")
    return languages


@task(name="Load data into DuckDB")
def load_task(repos: list[dict], languages: list[dict]) -> dict:
    logger = get_run_logger()
    con = get_connection()
    init_schema(con)

    repos_count = load_repos(con, repos)
    langs_count = load_languages(con, languages)
    con.close()

    summary = {"repos_loaded": repos_count, "languages_loaded": langs_count}
    logger.info(f"Load complete: {summary}")
    return summary


@task(name="Run dbt transformations")
def transform_task() -> bool:
    logger = get_run_logger()
    logger.info(f"Running dbt build in {DBT_DIR}...")

    result = subprocess.run(
        ["dbt", "build", "--profiles-dir", str(DBT_DIR)],
        cwd=str(DBT_DIR),
        capture_output=True,
        text=True,
    )

    logger.info(result.stdout)
    if result.returncode != 0:
        logger.error(result.stderr)
        raise RuntimeError(f"dbt build failed:\n{result.stderr}")

    logger.info("✅ dbt build succeeded")
    return True


# ── Flows ──────────────────────────────────────────────────────────────────────

@flow(name="GitHub ELT Pipeline", log_prints=True)
def run_pipeline(
    topics: list[str] = TOPICS,
    per_topic: int = REPOS_PER_TOPIC,
):
    """
    Full ELT pipeline:
    1. Extract repos + languages from GitHub API
    2. Load raw data into DuckDB
    3. Transform with dbt (staging → marts)
    """
    # Extract
    repos = extract_repos_task(topics=topics, per_topic=per_topic)
    languages = extract_languages_task(repos=repos)

    # Load
    load_summary = load_task(repos=repos, languages=languages)

    # Transform (runs after load completes)
    transform_task(wait_for=[load_summary])

    print(f"\n🎉 Pipeline complete — {load_summary}")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_pipeline()
