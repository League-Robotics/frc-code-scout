#!/usr/bin/env python3
"""Agent-confirmation scoring tier — "score what's USED, not present".

The mechanical pass (scout.features) measures *presence*; this tier hands an LLM agent the cited
evidence + the repo path and asks it to OPEN the files and confirm each rubric level. It is the only
way to push past the ~0.38 mechanical sophistication ceiling the EPA-prediction notebook found.

This module is a **driver/utility**, not a subprocess launcher: the model fan-out is orchestrated by
the Claude Code main loop (or `claude -p`), which calls the Agent tool once per (team, model) with
`build_prompt(...)` and the chosen model, then feeds the returned JSON back through `record()`.

CLI helpers:
    uv run python scripts/agent_score.py teams --n 6        # the stratified pilot team set
    uv run python scripts/agent_score.py packet --team 4738 # print one evidence packet (debug)
    uv run python scripts/agent_score.py prompt --team 4738 # print the full agent prompt

Outputs:
    data/agent-scores.csv               one row per (team, year[, model]) confirmed D1–D8
    tests/model-fidelity/<team>-<model>.json   per-(team,model) pilot score docs
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import pandas as pd

from scout import features

DIMS = features.DIMS
DIM_NAME = {"D1": "Architecture / hardware-decoupling", "D2": "Coordination & decision logic",
            "D3": "Simulation", "D4": "Testing & verification", "D5": "Logging & telemetry",
            "D6": "Autonomous & path planning", "D7": "Localization & vision",
            "D8": "Sustainability & process"}

# Output JSON the agent must return (half-steps allowed, 0–4 per dimension).
SCHEMA = {
    "team": "int", "year": "int",
    **{d: "number 0-4 (half-steps ok)" for d in DIMS},
    "rationale": {d: "one sentence: what you CONFIRMED by reading, and what you discounted" for d in DIMS},
    "evidence": {d: ["relative/path.java:line — the file you opened"] for d in DIMS},
    "confidence": "high | medium | low",
}


def _root() -> Path:
    for b in [Path.cwd(), *Path.cwd().parents]:
        if (b / "data" / "code-index.duckdb").exists():
            return b
    raise FileNotFoundError("run `python3 main.py index-db` first")


def connect(root: Path | None = None):
    root = root or _root()
    return duckdb.connect(str(root / "data" / "code-index.duckdb"), read_only=True)


def latest_repo(con, team: int) -> dict | None:
    """The team's latest cloned season + its primary repo (most files)."""
    yr = con.execute("""SELECT max(r.year) FROM repos r
        JOIN files f ON f.team=r.team AND f.year=r.year
        WHERE r.team=? AND r.bucket='season' AND r.cloned AND r.year>0""", [team]).fetchone()[0]
    if yr is None:
        return None
    row = con.execute("""SELECT r.repo, r.local_path, count(f.file_id) nf
        FROM repos r JOIN files f ON f.repo_id=r.repo_id
        WHERE r.team=? AND r.year=? AND r.bucket='season'
        GROUP BY r.repo, r.local_path ORDER BY nf DESC LIMIT 1""", [team, yr]).fetchone()
    name = con.execute("SELECT name FROM teams WHERE team=?", [team]).fetchone()[0]
    return {"team": team, "name": name, "year": int(yr), "repo": row[0],
            "local_path": row[1], "n_files": int(row[2])}


def pilot_teams(con, n: int = 6) -> list[int]:
    """Stratified across the mechanical candidate-total range + the Patribots (4738) anchor."""
    df = features.build(con)
    latest = df.sort_values("year").groupby("team").tail(1).copy()
    latest["total"] = latest.apply(lambda r: sum(features.candidate_levels(r).values()), axis=1)
    latest = latest[latest.team.isin([t for t in latest.team
                                      if latest_repo(con, int(t))])].sort_values("total")
    teams = list(latest.team)
    picks, k = [], len(teams)
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):       # low / Q1 / median / Q3 / high
        picks.append(int(teams[min(k - 1, int(frac * (k - 1)))]))
    if 4738 in teams and 4738 not in picks:        # always include the known anchor
        picks.append(4738)
    seen, out = set(), []
    for t in picks:                                 # de-dup, preserve order, cap at n
        if t not in seen:
            seen.add(t); out.append(t)
    return out[:n]


def _evidence(con, team: int, year: int) -> dict:
    """Concrete leads per dimension (names / files / counts) for the agent to VERIFY."""
    q = lambda s, p=(): con.execute(s, list(p)).fetchall()
    k = [team, year]
    def names(sql):
        return [r[0] for r in q(sql, k) if r[0]]
    return {
        "D1": {
            "io_interfaces": names("SELECT DISTINCT name FROM symbols WHERE team=? AND year=? AND kind='interface' AND name LIKE '%IO'"),
            "device_impls": names("SELECT DISTINCT name FROM symbols WHERE team=? AND year=? AND kind='class' AND (name LIKE '%IOTalonFX' OR name LIKE '%IOSparkMax' OR name LIKE '%IOKraken' OR name LIKE '%IOSim')"),
            "generic_base/servo": names("SELECT DISTINCT name FROM symbols WHERE team=? AND year=? AND (name LIKE '%MotorIO' OR name LIKE '%ServoMotorSubsystem')"),
            "vendor_imports_total": q("SELECT count(*) FROM imports WHERE team=? AND year=? AND (target LIKE 'com.ctre%' OR target LIKE 'com.revrobotics%' OR target LIKE 'org.photonvision%')", k)[0][0],
        },
        "D2": {
            "coordinators": names("SELECT DISTINCT name FROM symbols WHERE team=? AND year=? AND (name LIKE '%Superstructure' OR name LIKE '%RobotManager')"),
            "state_enums": names("SELECT DISTINCT name FROM symbols WHERE team=? AND year=? AND kind='enum' AND (name LIKE '%State' OR name LIKE '%Goal')"),
            "request_api/transitions": names("SELECT DISTINCT name FROM symbols WHERE team=? AND year=? AND kind='method' AND (name IN ('requestGoal','request') OR name LIKE 'handleState%')"),
        },
        "D3": {
            "maple_sim": q("SELECT count(*) FROM imports WHERE team=? AND year=? AND target LIKE 'org.ironmaple%'", k)[0][0],
            "wpilib_sim_ctors": q("SELECT coalesce(sum(n),0) FROM calls WHERE team=? AND year=? AND callee IN ('ElevatorSim','SingleJointedArmSim','FlywheelSim','DCMotorSim')", k)[0][0],
            "replay_classes": names("SELECT DISTINCT name FROM symbols WHERE team=? AND year=? AND (name LIKE '%IOReplay' OR name LIKE '%IONull')"),
        },
        "D4": {
            "test_files": q("SELECT count(*) FROM files WHERE team=? AND year=? AND file_path LIKE '%/test/%'", k)[0][0],
            "assert_calls": q("SELECT coalesce(sum(n),0) FROM calls WHERE team=? AND year=? AND callee LIKE 'assert%'", k)[0][0],
            "hal_harness": q("SELECT count(*) FROM imports WHERE team=? AND year=? AND target LIKE 'edu.wpi.first.hal%'", k)[0][0],
            "ci_workflow": q("SELECT count(*) FROM deploy_files WHERE team=? AND year=? AND kind='ci_workflow'", k)[0][0],
        },
        "D5": {
            "advantagekit": q("SELECT count(*) FROM imports WHERE team=? AND year=? AND target LIKE 'org.littletonrobotics.junction%'", k)[0][0],
            "autolog_anns": q("SELECT coalesce(sum(n),0) FROM annotations WHERE team=? AND year=? AND name='AutoLog'", k)[0][0],
            "recordOutput/processInputs": q("SELECT coalesce(sum(n),0) FROM calls WHERE team=? AND year=? AND callee IN ('recordOutput','processInputs')", k)[0][0],
            "doglog/epilogue": q("SELECT count(*) FROM imports WHERE team=? AND year=? AND (target LIKE 'dev.doglog%' OR target LIKE '%epilogue%')", k)[0][0],
        },
        "D6": {
            "pathplanner_files": q("SELECT count(*) FROM deploy_files WHERE team=? AND year=? AND kind LIKE 'pathplanner%'", k)[0][0],
            "choreo_files": q("SELECT count(*) FROM deploy_files WHERE team=? AND year=? AND kind='choreo'", k)[0][0],
            "choreo_USED_in_code": q("SELECT coalesce(sum(n),0) FROM calls WHERE team=? AND year=? AND callee='fromChoreoTrajectory'", k)[0][0],
            "pathfind/repulsor": q("SELECT coalesce(sum(n),0) FROM calls WHERE team=? AND year=? AND callee LIKE 'pathfind%'", k)[0][0],
        },
        "D7": {
            "photonvision": q("SELECT count(*) FROM imports WHERE team=? AND year=? AND target LIKE 'org.photonvision%'", k)[0][0],
            "addVisionMeasurement": q("SELECT coalesce(sum(n),0) FROM calls WHERE team=? AND year=? AND callee='addVisionMeasurement'", k)[0][0],
            "robotstate/vision_io": names("SELECT DISTINCT name FROM symbols WHERE team=? AND year=? AND (name LIKE '%RobotState' OR (kind='interface' AND name LIKE '%VisionIO'))"),
            "time_interp_buffer": q("SELECT count(*) FROM imports WHERE team=? AND year=? AND target LIKE '%TimeInterpolatableBuffer%'", k)[0][0],
        },
        "D8": {
            "seasons_tracked": q("SELECT count(DISTINCT year) FROM repos WHERE team=? AND bucket='season' AND cloned", [team])[0][0],
            "max_contributors": q("SELECT coalesce(max(contributors),0) FROM repos WHERE team=?", [team])[0][0],
            "has_library_repo": bool(q("SELECT bool_or(bucket='library') FROM repos WHERE team=? AND cloned", [team])[0][0]),
            "ci_workflows": q("SELECT count(*) FROM deploy_files WHERE team=? AND kind='ci_workflow'", [team])[0][0],
        },
    }


def evidence_packet(con, team: int) -> dict | None:
    info = latest_repo(con, team)
    if info is None:
        return None
    feat = features.build(con)
    row = feat[(feat.team == team) & (feat.year == info["year"])]
    cand = features.candidate_levels(row.iloc[0]) if len(row) else {d: None for d in DIMS}
    return {"info": info, "candidate": cand, "evidence": _evidence(con, team, info["year"])}


PROMPT = """You are scoring FRC team {name} (#{team}), {year} season, against the 8-dimension code
rubric in `knowledge/rubric/rubric.md`. The repository is on disk at:

    {repo_path}

THE GOLDEN RULE: score what is *USED*, not what is *present*. A mechanical pass already produced the
candidate levels and the leads below — they are starting points, NOT proof. You MUST open the cited
files (and search the repo) and confirm real, wired-in use before assigning each level. A Choreo
vendordep with no trajectories driven is not D6=3; an `*IO` interface with one impl is not a layer;
an empty `src/test` folder is not testing.

Mechanical candidate levels (verify or correct each): {candidate}

Per-dimension leads from the index (counts / names / files to check):
{evidence}

Rubric dimensions: {dims}

Score each D1–D8 on 0–4 (half-steps allowed). Read enough source to justify every level. Then WRITE
your result as a JSON file to:

    {out_path}

with exactly this shape (no extra prose in the file):
{schema}

Keep each rationale to one sentence naming what you confirmed and what you discounted. Put 1–3 real
`path:line` strings in each evidence list. Be skeptical and specific. After writing the file, reply
with ONLY one line: `team {team}: D1..D8 = <the eight values> (total <sum>)` — do not paste the JSON."""


def build_prompt(con, team: int) -> str | None:
    pk = evidence_packet(con, team)
    if pk is None:
        return None
    info = pk["info"]
    return PROMPT.format(
        name=info["name"], team=team, year=info["year"],
        repo_path=f"frc_team_repos/{info['local_path']}",
        candidate=json.dumps(pk["candidate"]),
        evidence=json.dumps(pk["evidence"], indent=2),
        dims="; ".join(f"{d} {DIM_NAME[d]}" for d in DIMS),
        schema=json.dumps(SCHEMA, indent=2),
        out_path=f"{SCORE_DIR}/{team}.json")


# --- result IO --------------------------------------------------------------------------------

def record(scores: dict, root: Path | None = None, model: str | None = None) -> None:
    """Append/replace one confirmed score row in data/agent-scores.csv (keyed team,year[,model])."""
    root = root or _root()
    path = root / "data" / "agent-scores.csv"
    row = {"team": int(scores["team"]), "year": int(scores["year"]),
           **{d: float(scores[d]) for d in DIMS},
           "total": float(sum(scores[d] for d in DIMS)),
           "confidence": scores.get("confidence", "")}
    if model:
        row["model"] = model
    df = pd.read_csv(path) if path.exists() else pd.DataFrame()
    keys = ["team", "year"] + (["model"] if model else [])
    if len(df):
        mask = pd.Series(True, index=df.index)
        for kcol in keys:
            mask &= df.get(kcol, pd.Series(dtype=object)) == row.get(kcol)
        df = df[~mask]
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, index=False)


def save_pilot(scores: dict, model: str, root: Path | None = None) -> Path:
    root = root or _root()
    d = root / "tests" / "model-fidelity"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{int(scores['team'])}-{model}.json"
    p.write_text(json.dumps({**scores, "model": model}, indent=2))
    return p


SCORE_DIR = "data/agent-scores"   # per-team JSON, written by each scoring agent (race-free)


def consolidate(root: Path | None = None) -> int:
    """Build data/agent-scores.csv from every data/agent-scores/<team>.json the agents wrote."""
    root = root or _root()
    d = root / SCORE_DIR
    rows = []
    for f in sorted(d.glob("*.json")):
        try:
            s = json.loads(f.read_text())
            rows.append({"team": int(s["team"]), "year": int(s["year"]),
                         **{dim: float(s[dim]) for dim in DIMS},
                         "total": float(sum(s[dim] for dim in DIMS)),
                         "confidence": s.get("confidence", "")})
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            print(f"  skip {f.name}: {e}")
    out = root / "data" / "agent-scores.csv"
    pd.DataFrame(rows).sort_values("total", ascending=False).to_csv(out, index=False)
    return len(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("teams"); t.add_argument("--n", type=int, default=6)
    p = sub.add_parser("packet"); p.add_argument("--team", type=int, required=True)
    pr = sub.add_parser("prompt"); pr.add_argument("--team", type=int, required=True)
    sub.add_parser("consolidate")
    args = ap.parse_args()
    if args.cmd == "consolidate":
        n = consolidate(); print(f"consolidated {n} team scores -> data/agent-scores.csv"); return
    con = connect()
    if args.cmd == "teams":
        ts = pilot_teams(con, args.n)
        for t_ in ts:
            info = latest_repo(con, t_)
            print(f"{t_:5d}  {info['name']:24s}  {info['year']}  {info['repo']}  ({info['n_files']} files)")
    elif args.cmd == "packet":
        print(json.dumps(evidence_packet(con, args.team), indent=2, default=str))
    elif args.cmd == "prompt":
        print(build_prompt(con, args.team))


if __name__ == "__main__":
    main()
