"""
pipeline/load.py
----------------
Loads extracted data into DuckDB (raw schema).

Design decisions:
- Raw tables are APPEND-ONLY with snapshot_at timestamp
  → lets us track evolution over time (stars growing, new repos appearing)
- Idempotent: re-running the pipeline on the same day won't duplicate rows
  (we delete today's snapshot before inserting)
"""

import os
import logging
from datetime import date

import duckdb
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DUCKDB_PATH", "./pipeline.duckdb")


def get_connection() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(DB_PATH)


def init_schema(con: duckdb.DuckDBPyConnection) -> None:
    """Create raw schema and tables if they don't exist."""
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    con.execute("""
        CREATE TABLE IF NOT EXISTS raw.repos (
            repo_id          INTEGER,
            name             VARCHAR,
            full_name        VARCHAR,
            owner_login      VARCHAR,
            owner_type       VARCHAR,
            description      VARCHAR,
            primary_language VARCHAR,
            stars            INTEGER,
            forks            INTEGER,
            open_issues      INTEGER,
            watchers         INTEGER,
            is_fork          BOOLEAN,
            is_archived      BOOLEAN,
            created_at       TIMESTAMP,
            pushed_at        TIMESTAMP,
            topics           VARCHAR,
            license          VARCHAR,
            html_url         VARCHAR,
            source_topic     VARCHAR,
            snapshot_at      TIMESTAMP
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS raw.repo_languages (
            repo_id     INTEGER,
            full_name   VARCHAR,
            language    VARCHAR,
            bytes       INTEGER,
            pct         DOUBLE,
            snapshot_at TIMESTAMP
        )
    """)

    logger.info("Schema initialized: raw.repos, raw.repo_languages")


def load_repos(con: duckdb.DuckDBPyConnection, repos: list[dict]) -> int:
    """
    Insert repos into raw.repos.
    Idempotent: deletes today's rows before inserting.
    """
    if not repos:
        logger.warning("No repos to load")
        return 0

    today = date.today().isoformat()

    # Remove today's snapshot to allow re-runs
    deleted = con.execute(
        "DELETE FROM raw.repos WHERE snapshot_at::date = ?", [today]
    ).rowcount
    if deleted:
        logger.info(f"Removed {deleted} existing rows for {today} (re-run)")

    # Bulk insert via DuckDB's fast from-dict method
    con.executemany("""
        INSERT INTO raw.repos VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, [list(r.values()) for r in repos])

    count = len(repos)
    logger.info(f"Loaded {count} repos into raw.repos")
    return count


def load_languages(con: duckdb.DuckDBPyConnection, languages: list[dict]) -> int:
    """
    Insert language breakdown into raw.repo_languages.
    Idempotent: deletes today's rows before inserting.
    """
    if not languages:
        logger.warning("No language data to load")
        return 0

    today = date.today().isoformat()

    deleted = con.execute(
        "DELETE FROM raw.repo_languages WHERE snapshot_at::date = ?", [today]
    ).rowcount
    if deleted:
        logger.info(f"Removed {deleted} existing language rows for {today} (re-run)")

    con.executemany("""
        INSERT INTO raw.repo_languages VALUES (?, ?, ?, ?, ?, ?)
    """, [list(r.values()) for r in languages])

    count = len(languages)
    logger.info(f"Loaded {count} language rows into raw.repo_languages")
    return count
