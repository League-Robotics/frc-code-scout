"""Command-line entry point and the build orchestration.

Subcommands:
  build        full pipeline: discover -> clone+history+suppress -> EPA -> dataset
  list-teams   print the merged, de-duplicated team list
  discover     print the repo plan for one team (no clone)
  epa          print Statbotics EPA for one team across the season window

The build is resumable: cached GitHub/Statbotics responses and skip-existing
clones mean a re-run continues where an interrupted one stopped.
"""

from __future__ import annotations

import argparse
import sys
import time

from . import clone, config, dataset, manifest, select, statbotics
from .teams import Team, load_teams


def _log(msg: str) -> None:
    print(f"[scout] {msg}", file=sys.stderr, flush=True)


def _filter_teams(teams: list[Team], wanted: list[int] | None, limit: int | None):
    if wanted:
        teams = [t for t in teams if t.number in set(wanted)]
    if limit:
        teams = teams[:limit]
    return teams


def _cache(sub: str):
    return config.CACHE_DIR / sub


def _process_team(team: Team, *, token, output_root, keep_git, do_clone) -> dict:
    team_dir = output_root / team.slug
    plan = select.plan_team_repos(team, token=token, cache_dir=_cache("github"))
    _log(
        f"team {team.number} {team.name}: {len(plan['selected'])} repos selected, "
        f"{len(plan['skipped'])} skipped"
    )

    repo_records: list[dict] = []
    for sel in plan["selected"]:
        if do_clone:
            rec = clone.process_repo(
                team_dir,
                year=sel["season"],
                repo_name=sel["repo"],
                clone_url=sel["clone_url"],
                html_url=sel["html_url"],
                keep_git=keep_git,
                output_root=output_root,
            )
        else:  # discovery-only record
            bucket = str(sel["season"]) if sel["season"] else "library"
            rec = {
                "year": sel["season"], "repo": sel["repo"], "url": sel["html_url"],
                "local_path": f"{team.slug}/{bucket}/{sel['repo']}", "cloned": False,
                "error": "skipped_clone",
            }
        rec["detected_via"] = sel["detected_via"]
        rec["fork"] = sel["fork"]
        rec["archived"] = sel["archived"]
        repo_records.append(rec)
        if rec.get("cloned"):
            sup = rec.get("suppressed_files", 0)
            hs = rec.get("history_summary") or {}
            _log(f"    + {sel['repo']} ({rec.get('year') or 'lib'}): "
                 f"{hs.get('commits', 0)} commits, {sup} suppressed")
        elif do_clone:
            _log(f"    ! {sel['repo']}: {rec.get('error')}")

    epa = [
        statbotics.fetch_team_year(team.number, y, cache_dir=_cache("statbotics"))
        for y in config.SEASON_WINDOW
    ]

    manifest.write_team_manifest(team_dir, team, plan, repo_records, epa)
    return dataset.build_team_entry(team, plan, repo_records, epa)


def cmd_build(args) -> int:
    output_root = config.resolve_output_root(args.output_root)
    config.warn_if_synced(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    token = args.token or config.github_token()
    if not token:
        _log("WARNING: no GITHUB_TOKEN/GH_TOKEN; anonymous API is 60 req/hr and will stall.")

    teams = _filter_teams(load_teams(), args.team, args.limit)
    _log(f"building corpus for {len(teams)} teams -> {output_root}")

    start = time.time()
    entries: list[dict] = []
    for i, team in enumerate(teams, 1):
        _log(f"[{i}/{len(teams)}] {team.number} {team.name}")
        try:
            entries.append(
                _process_team(
                    team, token=token, output_root=output_root,
                    keep_git=args.keep_git, do_clone=not args.no_clone,
                )
            )
        except Exception as e:  # never let one team kill the run
            _log(f"  ERROR on team {team.number}: {e}")
        if args.budget and (time.time() - start) > args.budget:
            _log(f"budget {args.budget}s exceeded; stopping after {i} teams (resumable).")
            break

    master = args.master_json or config.DEFAULT_MASTER_JSON
    inv = args.inventory or config.DEFAULT_INVENTORY_MD
    dataset.write_master(master, entries, output_root)
    dataset.write_inventory_md(inv, entries)
    _log(f"wrote {master} and {inv} ({len(entries)} teams)")
    return 0


def cmd_list_teams(args) -> int:
    for t in load_teams():
        print(f"{t.number:>5}  {t.name:<24} {'+'.join(t.sources):<18} "
              f"{','.join(t.owners)}  seeds={len(t.seed_repos)}")
    return 0


def cmd_discover(args) -> int:
    token = args.token or config.github_token()
    teams = {t.number: t for t in load_teams()}
    for num in args.team:
        t = teams.get(num)
        if not t:
            _log(f"team {num} not found")
            continue
        plan = select.plan_team_repos(t, token=token, cache_dir=_cache("github"))
        print(f"\n## {t.number} {t.name} (owners: {', '.join(t.owners)})")
        for s in plan["selected"]:
            print(f"  [{s['season'] or 'lib':>4}] {s['repo']:<40} via={s['detected_via']} "
                  f"fork={s['fork']} {s['html_url']}")
        print(f"  skipped: {len(plan['skipped'])} "
              f"({', '.join(s['repo'] for s in plan['skipped'][:8])}"
              f"{'...' if len(plan['skipped']) > 8 else ''})")
    return 0


def cmd_epa(args) -> int:
    for num in args.team:
        print(f"\n## team {num}")
        for y in config.SEASON_WINDOW:
            e = statbotics.fetch_team_year(num, y, cache_dir=_cache("statbotics"))
            if e["status"] == "ok":
                print(f"  {y}: normEPA={e['norm_EPA']} pts={e['epa_points']} "
                      f"winrate={e['winrate']} state%ile={e['state_pctile']}")
            else:
                print(f"  {y}: {e['status']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="scout", description="FRC team code corpus builder")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="run the full corpus build")
    b.add_argument("--output-root", help="corpus root (default: $SCOUT_DATA or ./frc_team_repos)")
    b.add_argument("--token", help="GitHub token (default: $GITHUB_TOKEN/$GH_TOKEN)")
    b.add_argument("--team", type=int, action="append", help="only this team (repeatable)")
    b.add_argument("--limit", type=int, help="cap number of teams (debug)")
    b.add_argument("--budget", type=int, help="stop after N seconds (resumable)")
    b.add_argument("--keep-git", action="store_true", help="keep .git blobs (default: strip)")
    b.add_argument("--no-clone", action="store_true", help="discover+EPA only, skip cloning")
    b.add_argument("--master-json", help="override master dataset path")
    b.add_argument("--inventory", help="override inventory markdown path")
    b.set_defaults(func=cmd_build)

    lt = sub.add_parser("list-teams", help="print the merged team list")
    lt.set_defaults(func=cmd_list_teams)

    d = sub.add_parser("discover", help="print the repo plan for a team")
    d.add_argument("--team", type=int, action="append", required=True)
    d.add_argument("--token")
    d.set_defaults(func=cmd_discover)

    e = sub.add_parser("epa", help="print Statbotics EPA for a team")
    e.add_argument("--team", type=int, action="append", required=True)
    e.set_defaults(func=cmd_epa)

    args = p.parse_args(argv)
    return args.func(args)
