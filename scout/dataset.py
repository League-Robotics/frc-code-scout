"""Assemble and write the master dataset (JSON) and the inventory report (Markdown).

The master JSON is the committed, distilled artifact: team list + provenance +
which repos went where (relative paths) + per-repo history summary + EPA by year.
It deliberately omits the per-commit detail (that lives in each repo's
history.json) and the raw EPA blocks (those live in per-team manifest.json) so it
stays scannable.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import config
from .teams import Team

# EPA keys kept in the master file (drop the verbose raw blocks).
_EPA_SLIM = (
    "year", "status", "norm_EPA", "epa_points", "unitless_epa",
    "state_pctile", "winrate", "wins", "losses", "ties",
)


def _slim_epa(epa: list[dict]) -> list[dict]:
    return [{k: e.get(k) for k in _EPA_SLIM if k in e} for e in epa]


def build_team_entry(
    team: Team, plan: dict, repo_records: list[dict], epa: list[dict]
) -> dict:
    return {
        "team": team.number,
        "name": team.name,
        "owners": team.owners,
        "sources": team.sources,
        "github_urls_visited": plan["urls_visited"],
        "repos": repo_records,
        "skipped_count": len(plan["skipped"]),
        "epa": _slim_epa(epa),
    }


def write_master(path: Path, entries: list[dict], output_root: Path) -> None:
    payload = {
        "generated": _today(),
        "output_root": str(output_root),
        "seasons": {str(y): n for y, n in config.SEASONS.items()},
        "season_window": list(config.SEASON_WINDOW),
        "suppress": {
            "size_threshold_bytes": config.SUPPRESS_SIZE_BYTES,
            "extensions": sorted(config.SUPPRESS_EXTS),
        },
        "team_count": len(entries),
        "teams": entries,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1))


def _today() -> str:
    # Avoid Date.now-style nondeterminism in the module; the CLI stamps via git.
    import datetime
    return datetime.date.today().isoformat()


# --- Inventory markdown ----------------------------------------------------

def write_inventory_md(path: Path, entries: list[dict]) -> None:
    lines: list[str] = []
    lines.append("# FRC Team Code Corpus — Inventory\n")
    lines.append(
        f"Generated {_today()}. {len(entries)} teams "
        f"({sum('national' in e['sources'] for e in entries)} national, "
        f"{sum('sandiego' in e['sources'] for e in entries)} San Diego, "
        f"{sum(len(e['sources']) == 2 for e in entries)} both). "
        f"Seasons {config.SEASON_WINDOW[0]}–{config.SEASON_WINDOW[-1]}. "
        "Git history is captured as per-repo `history.json` (no blobs kept); "
        "large files suppressed to `*.sup` stubs.\n"
    )

    # Summary table
    lines.append("## Summary\n")
    lines.append("| Team | Name | Source | Repos cloned | Seasons | Latest normEPA |")
    lines.append("|---|---|---|---|---|---|")
    for e in sorted(entries, key=lambda x: x["team"]):
        cloned = [r for r in e["repos"] if r.get("cloned")]
        years = sorted({r["year"] for r in cloned if r.get("year")}, reverse=True)
        latest_epa = _latest_norm_epa(e["epa"])
        src = "+".join("N" if s == "national" else "SD" for s in e["sources"])
        lines.append(
            f"| {e['team']} | {e['name']} | {src} | {len(cloned)} | "
            f"{', '.join(map(str, years)) or '—'} | {latest_epa} |"
        )
    lines.append("")

    # Per-team detail
    lines.append("## Teams\n")
    for e in sorted(entries, key=lambda x: x["team"]):
        lines.append(f"### {e['team']} — {e['name']}  ({', '.join(e['sources'])})\n")
        lines.append(f"GitHub: {', '.join(e['owners'])}\n")
        lines.append("**Repos**")
        lines.append("")
        lines.append("| Year | Repo | Commits | Churn (＋/−) | Contributors | Status |")
        lines.append("|---|---|---|---|---|---|")
        for r in sorted(e["repos"], key=lambda x: (-(x.get("year") or 0), x["repo"].lower())):
            hs = r.get("history_summary") or {}
            churn = f"{hs.get('insertions', '?')}/{hs.get('deletions', '?')}" if hs else "—"
            status = "ok" if r.get("cloned") else f"FAIL ({r.get('error', '?')})"
            yr = r.get("year") or "lib"
            lines.append(
                f"| {yr} | {r['repo']} | {hs.get('commits', '—')} | {churn} | "
                f"{hs.get('contributors', '—')} | {status} |"
            )
        lines.append("")
        lines.append("**EPA by year**")
        lines.append("")
        lines.append("| Year | normEPA | EPA pts | winrate | state %ile |")
        lines.append("|---|---|---|---|---|")
        for ep in sorted(e["epa"], key=lambda x: x.get("year", 0)):
            if ep.get("status") != "ok":
                lines.append(f"| {ep.get('year')} | — | — | — | {ep.get('status')} |")
            else:
                lines.append(
                    f"| {ep['year']} | {ep.get('norm_EPA')} | {ep.get('epa_points')} | "
                    f"{ep.get('winrate')} | {ep.get('state_pctile')} |"
                )
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def _latest_norm_epa(epa: list[dict]):
    ok = [e for e in epa if e.get("status") == "ok" and e.get("norm_EPA") is not None]
    if not ok:
        return "—"
    return max(ok, key=lambda e: e["year"])["norm_EPA"]
