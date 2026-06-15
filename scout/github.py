"""GitHub repo discovery via the REST API (paginated, token-authed).

Ports the pattern from scripts/discover_repos.sh (users/{owner}/repos, fork
filter) but paginates fully and returns structured records instead of a TSV line.
The `users/{owner}/repos` endpoint serves both users and organizations.
"""

from __future__ import annotations

from pathlib import Path

from . import config
from .httpc import HttpError, get_json


def list_owner_repos(
    owner: str, *, token: str | None, cache_dir: Path | None
) -> tuple[list[dict], list[str]]:
    """List an owner's repos. Returns (repos, api_urls_visited).

    Each repo dict: name, fork, archived, pushed_at, html_url, clone_url,
    default_branch, size. Forks are kept here; selection logic decides relevance.
    """
    repos: list[dict] = []
    visited: list[str] = []
    page = 1
    while True:
        url = (
            f"{config.GITHUB_API}/users/{owner}/repos"
            f"?per_page=100&page={page}&sort=pushed&type=owner"
        )
        visited.append(url)
        cache_path = cache_dir / f"github-{owner}-p{page}.json" if cache_dir else None
        try:
            batch = get_json(url, token=token, cache_path=cache_path)
        except HttpError as e:
            if e.status == 404:  # owner not found / renamed
                break
            raise
        if not isinstance(batch, list) or not batch:
            break
        for r in batch:
            repos.append(
                {
                    "name": r["name"],
                    "fork": bool(r.get("fork")),
                    "archived": bool(r.get("archived")),
                    "pushed_at": r.get("pushed_at"),
                    "html_url": r["html_url"],
                    "clone_url": r.get("clone_url") or f"{r['html_url']}.git",
                    "default_branch": r.get("default_branch"),
                    "size_kb": r.get("size", 0),
                }
            )
        if len(batch) < 100:
            break
        page += 1
    return repos, visited
