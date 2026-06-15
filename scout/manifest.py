"""Per-team manifest written inside each team's corpus directory.

Records every GitHub URL visited to assemble that team's code (requirement 6),
plus the per-repo outcome, the skipped repos, and full EPA (including raw blocks).
"""

from __future__ import annotations

import json
from pathlib import Path

from .teams import Team


def write_team_manifest(
    team_dir: Path, team: Team, plan: dict, repo_records: list[dict], epa: list[dict]
) -> Path:
    team_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "team": team.number,
        "name": team.name,
        "owners": team.owners,
        "sources": team.sources,
        "github_urls_visited": plan["urls_visited"],
        "repos": repo_records,
        "skipped": plan["skipped"],
        "epa": epa,
    }
    out = team_dir / "manifest.json"
    out.write_text(json.dumps(payload, indent=1))
    return out
