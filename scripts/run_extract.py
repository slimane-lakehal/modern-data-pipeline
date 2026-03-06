"""
scripts/run_extract.py
----------------------
Runs extract + load without Prefect (useful for testing locally
before setting up the full orchestration).

Usage:
    python scripts/run_extract.py
"""

import logging
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")

from pipeline.extract import fetch_trending_repos, fetch_languages
from pipeline.load import get_connection, init_schema, load_repos, load_languages

TOPICS = [t.strip() for t in os.getenv("GITHUB_TOPICS", "data-engineering,dbt,python").split(",")]

def main():
    print(f"\n Topics: {TOPICS}")

    # Extract
    repos = fetch_trending_repos(topics=TOPICS, per_topic=30)
    print(f"Extracted {len(repos)} repos")

    languages = list(fetch_languages(repos))
    print(f"Extracted {len(languages)} language records")

    # Load
    con = get_connection()
    init_schema(con)
    load_repos(con, repos)
    load_languages(con, languages)
    con.close()

    print("\nData loaded into pipeline.duckdb")
    print("Run 'make transform' to build dbt models")

if __name__ == "__main__":
    main()
