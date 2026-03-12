"""
pipeline/extract.py
-------------------
Extracts trending GitHub repositories and their language breakdown
via the GitHub REST API.

What we fetch:
- Top repos per topic (stars, forks, open issues, description...)
- Language bytes per repo (e.g. Python: 45000, SQL: 12000)
- Snapshot timestamp for time-series tracking
"""

import os
import time
import logging
from datetime import datetime, timezone
from typing import Generator

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Inject token if available (raises rate limit from 60 → 5000 req/hr)
if token := os.getenv("GITHUB_TOKEN"):
    HEADERS["Authorization"] = f"Bearer {token}"
else:
    logger.warning("No GITHUB_TOKEN found. Rate limit: 60 req/hr.")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get(url: str, params: dict = None) -> dict:
    """GET with basic retry on rate limit (HTTP 403/429)."""
    for attempt in range(3):
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)

        if response.status_code == 200:
            return response.json()

        if response.status_code in (403, 429):
            wait = int(response.headers.get("Retry-After", 60))
            logger.warning(f"Rate limited. Waiting {wait}s... (attempt {attempt+1})")
            time.sleep(wait)
            continue

        response.raise_for_status()

    raise RuntimeError(f"Failed to fetch {url} after 3 attempts")


# ── Extractors ─────────────────────────────────────────────────────────────────

def fetch_trending_repos(
    topics: list[str],
    per_topic: int = 50,
    min_stars: int = 100,
) -> list[dict]:
    """
    Fetch top repositories for a list of topics.

    Returns a flat list of repo dicts, deduplicated by repo_id.
    Each dict is one row in our raw.repos table.
    """
    snapshot_at = datetime.now(timezone.utc).isoformat()
    seen_ids: set[int] = set()
    repos: list[dict] = []

    for topic in topics:
        logger.info(f"Fetching repos for topic: {topic}")

        # GitHub search API — sorted by stars descending
        data = _get(
            f"{GITHUB_API_URL}/search/repositories",
            params={
                "q": f"topic:{topic} stars:>={min_stars}",
                "sort": "stars",
                "order": "desc",
                "per_page": min(per_topic, 100),
            }
        )

        for item in data.get("items", []):
            repo_id = item["id"]

            # Deduplicate — a repo can appear in multiple topics
            if repo_id in seen_ids:
                continue
            seen_ids.add(repo_id)

            repos.append({
                "repo_id":          repo_id,
                "name":             item["name"],
                "full_name":        item["full_name"],
                "owner_login":      item["owner"]["login"],
                "owner_type":       item["owner"]["type"],      # User or Organization
                "description":      item.get("description"),
                "primary_language": item.get("language"),
                "stars":            item["stargazers_count"],
                "forks":            item["forks_count"],
                "open_issues":      item["open_issues_count"],
                "watchers":         item["watchers_count"],
                "is_fork":          item["fork"],
                "is_archived":      item["archived"],
                "created_at":       item["created_at"],
                "pushed_at":        item["pushed_at"],          # last commit
                "topics":           ",".join(item.get("topics", [])),
                "license":          item.get("license", {}).get("spdx_id") if item.get("license") else None,
                "html_url":         item["html_url"],
                "source_topic":     topic,                      # which query found it
                "snapshot_at":      snapshot_at,
            })

        # Be polite with the API — small sleep between topic queries
        time.sleep(1)

    logger.info(f"Fetched {len(repos)} unique repos across {len(topics)} topics")
    return repos


def fetch_languages(repos: list[dict]) -> Generator[dict, None, None]:
    """
    Fetch language breakdown for each repo.

    GitHub returns bytes per language, e.g.:
    {"Python": 45231, "SQL": 12000, "Shell": 800}

    Yields one dict per language per repo → normalized table.
    """
    snapshot_at = datetime.now(timezone.utc).isoformat()

    for i, repo in enumerate(repos, 1):
        full_name = repo["full_name"]
        logger.info(f"[{i}/{len(repos)}] Fetching languages for {full_name}")

        try:
            lang_data = _get(f"{GITHUB_API_URL}/repos/{full_name}/languages")
        except Exception as e:
            logger.warning(f"Skipping {full_name}: {e}")
            continue

        total_bytes = sum(lang_data.values()) or 1  # avoid division by zero

        for language, byte_count in lang_data.items():
            yield {
                "repo_id":    repo["repo_id"],
                "full_name":  full_name,
                "language":   language,
                "bytes":      byte_count,
                "pct":        round(byte_count / total_bytes * 100, 2),
                "snapshot_at": snapshot_at,
            }

        time.sleep(0.5)  # stay under rate limit

if __name__ == "__main__":
    repos = fetch_trending_repos(['python'])
    breakdown=list(fetch_languages(repos))
    
    for repo in breakdown[:5]:
        print(repo)