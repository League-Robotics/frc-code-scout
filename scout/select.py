"""Decide which of a team's repos to clone, and assign each a season.

Selection = (curated manifest repos, always) ∪ (discovered repos whose NAME
detects an in-window season). Discovered season-less / tooling repos are skipped
unless curated, which keeps websites and scouting apps out of the code corpus.
Out-of-window season repos (e.g. 2014) are recorded as skipped.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import config, github, seasons
from .teams import Team

_YEARISH = re.compile(r"20\d{2}|2k\d{2}", re.IGNORECASE)

# Substrings that mark a discovered repo as non-robot tooling even when its name
# carries a season year (e.g. "FLLScoring2024", "ScoutingCode2022"). Applied ONLY
# to discovered, non-curated repos — a curated manifest entry always wins.
_TOOLING_MARKERS = (
    "scouting", "fllscoring", "fll-", "website", "dashboard", "blog",
    "stats-api", ".github",
)


def _is_tooling(name: str) -> bool:
    low = name.lower()
    if low == ".github":
        return True
    return any(m in low for m in _TOOLING_MARKERS)


def _detected_via(name: str, season: int | None) -> str:
    if season is None:
        return "none"
    return "year" if _YEARISH.search(name) else "season-name"


def plan_team_repos(team: Team, *, token: str | None, cache_dir: Path | None) -> dict:
    """Discover and classify a team's repos. Returns a plan dict.

    {
      "urls_visited": [...api + repo urls...],
      "selected":  [{repo, season, detected_via, clone_url, html_url, discovered}],
      "skipped":   [{repo, reason, year}],
    }
    """
    discovered: dict[str, dict] = {}
    urls_visited: list[str] = []
    for owner in team.owners:
        repos, visited = github.list_owner_repos(owner, token=token, cache_dir=cache_dir)
        urls_visited.extend(visited)
        for r in repos:
            discovered.setdefault(r["name"], r)  # first owner wins on name clash

    seed = set(team.seed_repos)
    selected: list[dict] = []
    skipped: list[dict] = []
    chosen: set[str] = set()

    for name, r in discovered.items():
        season = seasons.detect_season(name)
        curated = name in seed
        if not curated and _is_tooling(name):
            skipped.append({"repo": name, "reason": "tooling", "year": season})
            continue
        if curated or season in config.SEASONS:
            selected.append(
                {
                    "repo": name,
                    "season": season,
                    "detected_via": _detected_via(name, season),
                    "clone_url": r["clone_url"],
                    "html_url": r["html_url"],
                    "discovered": True,
                    "fork": r["fork"],
                    "archived": r["archived"],
                }
            )
            chosen.add(name)
        else:
            old = seasons.detected_year_any(name)
            reason = f"old-season-{old}" if old else "no-season/library"
            skipped.append({"repo": name, "reason": reason, "year": old})

    # Curated repos that discovery didn't surface (renamed / deleted / private):
    # attempt them anyway, constructing a URL from the team's first owner.
    owner0 = team.owners[0] if team.owners else None
    for name in team.seed_repos:
        if name in chosen or owner0 is None:
            continue
        season = seasons.detect_season(name)
        selected.append(
            {
                "repo": name,
                "season": season,
                "detected_via": _detected_via(name, season),
                "clone_url": f"https://github.com/{owner0}/{name}.git",
                "html_url": f"https://github.com/{owner0}/{name}",
                "discovered": False,
                "fork": None,
                "archived": None,
            }
        )
        chosen.add(name)

    # Stable order: by season (newest first, library last), then name.
    selected.sort(key=lambda s: (-(s["season"] or 0), s["repo"].lower()))
    urls_visited.extend(s["html_url"] for s in selected)
    return {"urls_visited": urls_visited, "selected": selected, "skipped": skipped}
