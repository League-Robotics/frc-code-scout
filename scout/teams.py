"""Load and merge the two team sources into one de-duplicated list.

Sources:
  * data/manifests/frc-teams.tsv          (San Diego FRC, curated repo lists)
  * data/manifests/national-frc-teams.tsv (37 national teams, one seed repo each)

Teams present in both (e.g. 3128, 1538, 6995) collapse to a single record whose
`sources` carries both provenances.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import config


@dataclass
class Team:
    number: int
    name: str
    owners: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)  # "sandiego" / "national"
    seed_repos: list[str] = field(default_factory=list)

    @property
    def slug(self) -> str:
        """Filesystem-safe directory name: `<number>-<name>`."""
        safe = re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-")
        return f"{self.number}-{safe or 'team'}"


def _slug_name(raw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")


def load_manifest_tsv(path: Path) -> list[tuple[int, str, str, list[str]]]:
    """Parse a `team_id  name  owner  space-separated-repos` TSV (skips header)."""
    rows: list[tuple[int, str, str, list[str]]] = []
    if not path.exists():
        return rows
    for i, line in enumerate(path.read_text().splitlines()):
        if i == 0 or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        tid_raw, name, owner = parts[0], parts[1], parts[2]
        repos = parts[3].split() if len(parts) > 3 and parts[3].strip() else []
        try:
            tid = int(tid_raw.lstrip("0") or "0")
        except ValueError:
            continue
        rows.append((tid, _slug_name(name), owner.strip(), repos))
    return rows


def _merge_into(teams: dict[int, Team], rows, source: str, prefer_name: bool):
    for tid, name, owner, repos in rows:
        t = teams.get(tid)
        if t is None:
            teams[tid] = Team(
                number=tid, name=name, owners=[owner] if owner else [],
                sources=[source], seed_repos=list(repos),
            )
            continue
        if source not in t.sources:
            t.sources.append(source)
        if prefer_name and name:
            t.name = name
        if owner and owner not in t.owners:
            t.owners.append(owner)
        for r in repos:
            if r not in t.seed_repos:
                t.seed_repos.append(r)


def load_teams(
    sd_manifest: Path = config.SD_MANIFEST,
    national_manifest: Path = config.NATIONAL_MANIFEST,
) -> list[Team]:
    """Return all teams, de-duplicated by team number.

    San Diego rows load first (authoritative local names); national rows merge
    in, adding the 'national' provenance and any owner/seed repos not present.
    """
    teams: dict[int, Team] = {}
    _merge_into(teams, load_manifest_tsv(sd_manifest), "sandiego", prefer_name=True)
    _merge_into(teams, load_manifest_tsv(national_manifest), "national", prefer_name=False)
    return [teams[n] for n in sorted(teams)]
