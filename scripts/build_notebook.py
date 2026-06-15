#!/usr/bin/env python3
"""Assemble and execute the FRC corpus analysis notebook.

Builds notebooks/frc-code-analysis.ipynb from the cells defined below, runs it
against data/code-index.duckdb so every chart/table is embedded, and writes the
executed notebook. Re-run after re-indexing to refresh.

    uv run python scripts/build_notebook.py

Convention: cell sources are r"...". delimited; all inner multi-line SQL uses
triple-single-quotes so it never closes the cell string.
"""

from __future__ import annotations

from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "frc-code-analysis.ipynb"

CELLS: list[tuple[str, str]] = []


def md(src: str):
    CELLS.append(("md", src.strip("\n")))


def code(src: str):
    CELLS.append(("code", src.strip("\n")))


# ───────────────────────────────────────────────────────────────────────────
md(r"""
# Inside FRC Team Software — A Data View

**63 teams · 5 seasons (2022–2026) · ~39k source files, parsed with tree-sitter into DuckDB.**

This notebook reads `data/code-index.duckdb` — a structural index of every San Diego
and national-survey FRC team's robot code, joined to their commit history and
[Statbotics](https://statbotics.io) EPA. It answers five questions:

1. **Seasonality** — *when* during the year does the software work actually happen?
2. **Frameworks** — what libraries do teams adopt, and how is adoption spreading?
3. **The rubric, automated** — candidate D1–D8 scores for all 63 teams, validated
   against the 24 hand-scored teams.
4. **Testing & simulation** — who invests in verification (the rarest markers)?
5. **Does better code win?** — code sophistication vs. competition results.

> **Caveats.** The index holds *declarations, imports, calls, annotations* and
> *deploy files* — not full call graphs. Public "daily-mirror" repos (6328, 254)
> publish **squashed** history, so seasonality/sustainability filter to repos with
> real history (`commits > 30`). Rubric scores here are **candidates** — the
> project's rule is *score what's used, confirm by reading.*
""")

code(r"""
import duckdb, pandas as pd, numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
%matplotlib inline

plt.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": .25,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "figure.figsize": (9, 4.5), "font.size": 10})
ACC, ACC2, ACC3 = "#2563eb", "#f59e0b", "#10b981"

# Resolve the repo root by walking up from the kernel's cwd, so the notebook
# works whether it's launched from the repo root or from notebooks/.
def _root():
    for base in [Path.cwd(), *Path.cwd().parents]:
        if (base / "data" / "code-index.duckdb").exists():
            return base
    raise FileNotFoundError("data/code-index.duckdb not found — run `python3 main.py index-db`")
ROOT = _root()

con = duckdb.connect(str(ROOT / "data" / "code-index.duckdb"), read_only=True)
def q(sql): return con.execute(sql).df()

# Spearman = Pearson on ranks (avoids a scipy dependency).
def spearman(a, b): return a.rank().corr(b.rank())

# FRC competition calendar (month -> phase): build Jan–Feb, comp Mar–Apr, else offseason.
def phase(m): return "build" if m in (1, 2) else "competition" if m in (3, 4) else "offseason"

print("tables:", ", ".join(sorted(r[0] for r in con.execute("SHOW TABLES").fetchall())))
q('''SELECT (SELECT count(*) FROM teams) teams, (SELECT count(*) FROM repos) repos,
       (SELECT count(*) FROM files) files, (SELECT count(*) FROM symbols) symbols,
       (SELECT count(*) FROM calls) calls, (SELECT count(*) FROM commits) commits''')
""")

# ── Corpus overview ────────────────────────────────────────────────────────
md(r"""
## 1 · The corpus at a glance

Two populations — the **national survey** teams (architectural reference set) and the
**San Diego** teams — de-duplicated by team number, plus a `library/` bucket for
season-independent code.
""")

code(r"""
overview = q('''
SELECT
  count(DISTINCT team) FILTER (WHERE list_contains(sources,'national')) AS national,
  count(DISTINCT team) FILTER (WHERE list_contains(sources,'sandiego')) AS san_diego,
  count(DISTINCT team) FILTER (WHERE len(sources)=2)                    AS both
FROM teams''')
display(overview)

fig, ax = plt.subplots(1, 2, figsize=(12, 4))
lang = q("SELECT lang, count(*) files, sum(line_count) loc FROM files GROUP BY lang ORDER BY files DESC")
ax[0].bar(lang.lang, lang.files, color=ACC); ax[0].set_title("Source files by language"); ax[0].set_ylabel("files")
top = q('''SELECT t.team||' '||t.name AS team, count(*) files FROM files f JOIN teams t USING(team)
           GROUP BY 1 ORDER BY files DESC LIMIT 15''')
ax[1].barh(top.team[::-1], top.files[::-1], color=ACC3); ax[1].set_title("Most code (files indexed)")
plt.tight_layout(); plt.show()
""")

# ── Seasonality ────────────────────────────────────────────────────────────
md(r"""
## 2 · Seasonality of effort — *when* does the software get written?

Using the commit history of every real-history season repo, mapped onto the FRC
calendar: **build** (Jan–Feb), **competition** (Mar–Apr), **offseason** (May–Dec).
""")

code(r"""
commits = q('''
SELECT c.committed_at, c.insertions + c.deletions AS churn, r.team, r.year
FROM commits c JOIN repos r ON r.repo_id = c.repo_id
WHERE r.bucket='season' AND r.commits > 30           -- drop squashed public mirrors
  AND c.committed_at IS NOT NULL
  AND extract(year FROM c.committed_at) BETWEEN 2021 AND 2026
''')
commits["month"] = commits.committed_at.dt.month
commits["phase"] = commits.month.map(phase)

fig, ax = plt.subplots(1, 2, figsize=(13, 4.3))
bym = commits.groupby("month").size().reindex(range(1, 13), fill_value=0)
colors = ["#2563eb" if m in (1,2) else "#ef4444" if m in (3,4) else "#9ca3af" for m in range(1,13)]
ax[0].bar(range(1, 13), bym.values, color=colors)
ax[0].set_xticks(range(1,13)); ax[0].set_xticklabels(list("JFMAMJJASOND"))
ax[0].set_title("Commits by calendar month (all teams)\nblue=build  red=competition  grey=offseason")
ax[0].set_ylabel("commits")

split = commits.groupby("phase").churn.sum().reindex(["build","competition","offseason"]).fillna(0)
ax[1].pie(split, labels=[f"{p}\n{v/split.sum():.0%}" for p,v in split.items()],
          colors=["#2563eb","#ef4444","#9ca3af"], startangle=90, wedgeprops=dict(width=.45))
ax[1].set_title("Share of code churn by season phase")
plt.tight_layout(); plt.show()
print(f"{len(commits):,} commits across {commits.team.nunique()} teams with real history")
""")

md(r"""
**Front-loaded or last-minute?** A repo's *center of mass* is the average day-of-year
of its commits. Lower = work lands early; higher = late-season or offseason work.
""")

code(r"""
com = q('''
SELECT r.team, t.name, r.year,
       avg(extract(doy FROM c.committed_at)) AS center_doy, count(*) AS commits
FROM commits c JOIN repos r ON r.repo_id=c.repo_id JOIN teams t ON t.team=r.team
WHERE r.bucket='season' AND r.commits>30 AND c.committed_at IS NOT NULL
GROUP BY r.team, t.name, r.year HAVING commits>30
''')
fig, ax = plt.subplots(figsize=(10, 4))
ax.hist(com.center_doy, bins=24, color=ACC, alpha=.85)
for d,l in [(46,"end of build (mid-Feb)"),(120,"end of comp (end-Apr)")]:
    ax.axvline(d, color="#ef4444", ls="--", lw=1); ax.text(d+3, ax.get_ylim()[1]*.88, l, fontsize=8, color="#ef4444")
ax.set_xlabel("center of mass (day of year)"); ax.set_ylabel("team-seasons")
ax.set_title("When the average commit lands")
plt.tight_layout(); plt.show()
print("Most offseason-heavy team-seasons:")
display(com.sort_values("center_doy", ascending=False).head(8).round(0).reset_index(drop=True))
""")

# ── Frameworks ─────────────────────────────────────────────────────────────
md(r"""
## 3 · Framework adoption

From the `imports` table — the cleanest adoption signal.
""")

code(r"""
FRAMEWORKS = {
  "AdvantageKit":"org.littletonrobotics.junction%", "PathPlanner":"com.pathplanner%",
  "Choreo":"choreo%", "PhotonVision":"org.photonvision%", "maple-sim":"org.ironmaple%",
  "DogLog":"dev.doglog%", "YAGSL":"swervelib%",
}
sel = ",\n".join(f'''count(DISTINCT team) FILTER (WHERE target LIKE '{p}') AS "{n}"''' for n,p in FRAMEWORKS.items())
adopt = q(f"SELECT year, {sel} FROM imports WHERE year BETWEEN 2022 AND 2026 GROUP BY year ORDER BY year")
display(adopt.set_index("year"))

fig, ax = plt.subplots(figsize=(10, 4.5))
for n in FRAMEWORKS:
    ax.plot(adopt.year, adopt[n], marker="o", label=n)
ax.set_xticks(range(2022,2027)); ax.set_ylabel("teams using"); ax.set_title("Framework adoption by season")
ax.legend(ncol=2, fontsize=8); plt.tight_layout(); plt.show()
""")

# ── Rubric pass ────────────────────────────────────────────────────────────
md(r"""
## 4 · The 8-dimension rubric, computed in SQL

Candidate D1–D8 for every team's latest season repo — the grep cheat-sheet across all
63 teams at once — validated against the 24 hand-scored teams in `sd-frc-master.csv`.
""")

code(r"""
f_sym = q('''SELECT team,year,
  count(*) FILTER (WHERE kind='interface' AND name LIKE '%IO') io_iface,
  count(*) FILTER (WHERE kind='class' AND name LIKE '%IOSim') io_sim,
  count(*) FILTER (WHERE kind='class' AND (name LIKE '%IOReal' OR name LIKE '%IOTalonFX')) io_real,
  count(*) FILTER (WHERE name LIKE '%IONull' OR name LIKE '%IOReplay' OR name LIKE '%IdealSim') io_adv,
  count(*) FILTER (WHERE name LIKE '%ServoMotorSubsystem') servomotor,
  count(*) FILTER (WHERE name LIKE '%Superstructure' OR name LIKE '%RobotManager') coordinator,
  count(*) FILTER (WHERE kind='enum' AND (name LIKE '%WantedState' OR name LIKE '%SystemState')) fsm,
  count(*) FILTER (WHERE name LIKE '%AStarSolver' OR name LIKE '%BehaviorTree%') graph,
  count(*) FILTER (WHERE name='simulationPeriodic') sim_periodic,
  count(*) FILTER (WHERE name LIKE '%RobotState') robotstate,
  count(*) FILTER (WHERE name LIKE '%Repulsor') repulsor,
  count(*) FILTER (WHERE name LIKE '%FaultReporter') faultreporter,
  count(*) FILTER (WHERE name LIKE '%TunerConstants') tuner
  FROM symbols GROUP BY team,year''')
f_imp = q('''SELECT team,year,
  count(*) FILTER (WHERE target LIKE 'org.littletonrobotics.junction%') advantagekit,
  count(*) FILTER (WHERE target LIKE 'com.pathplanner%') pathplanner,
  count(*) FILTER (WHERE target LIKE 'choreo%') choreo,
  count(*) FILTER (WHERE target LIKE 'org.photonvision%') photon,
  count(*) FILTER (WHERE target LIKE 'org.ironmaple%') maple,
  count(*) FILTER (WHERE target LIKE 'dev.doglog%') doglog,
  count(*) FILTER (WHERE target LIKE '%epilogue%') epilogue,
  count(*) FILTER (WHERE target LIKE 'swervelib%') yagsl,
  count(*) FILTER (WHERE target LIKE '%wpilibj.simulation%') wpilib_sim,
  count(*) FILTER (WHERE target LIKE 'org.jgrapht%') jgrapht,
  count(*) FILTER (WHERE target LIKE 'org.junit%') junit,
  count(*) FILTER (WHERE target LIKE '%LimelightHelpers%') limelight,
  count(*) FILTER (WHERE target LIKE '%PoseEstimator%') poseest
  FROM imports GROUP BY team,year''')
f_call = q('''SELECT team,year,
  sum(n) FILTER (WHERE callee='addVisionMeasurement') addvision,
  sum(n) FILTER (WHERE callee='processInputs') processinputs,
  sum(n) FILTER (WHERE callee='assertEquals') asserts,
  sum(n) FILTER (WHERE callee='runToCompletion') runtocompletion,
  sum(n) FILTER (WHERE callee LIKE 'put%') dashboard
  FROM calls GROUP BY team,year''')
f_ann = q('''SELECT team,year,
  sum(n) FILTER (WHERE name='AutoLog') AS autolog,
  sum(n) FILTER (WHERE name IN ('Logged','Epilogue')) AS logged,
  sum(n) FILTER (WHERE name='Test') AS test_ann
  FROM annotations GROUP BY team,year''')
f_dep = q('''SELECT team,year,
  count(*) FILTER (WHERE kind LIKE 'pathplanner%') AS pp_files,
  count(*) FILTER (WHERE kind='choreo') AS choreo_files,
  count(*) FILTER (WHERE kind='ci_workflow') AS ci,
  count(*) FILTER (WHERE kind='swerve_config') AS swerve
  FROM deploy_files GROUP BY team,year''')
f_file = q('''SELECT team,year, count(*) files, sum(line_count) loc,
  count(*) FILTER (WHERE file_path LIKE '%/test/%') test_files FROM files GROUP BY team,year''')

feat = f_file
for d in (f_sym, f_imp, f_call, f_ann, f_dep):
    feat = feat.merge(d, on=["team","year"], how="left")
feat = feat.fillna(0)

d8 = q('''SELECT team, count(DISTINCT year) FILTER (WHERE bucket='season') AS seasons,
                 max(contributors) AS contributors, bool_or(bucket='library') AS has_library
          FROM repos WHERE cloned GROUP BY team''')
ci_team = q("SELECT team, count(*) ci_any FROM deploy_files WHERE kind='ci_workflow' GROUP BY team")

# score each team on its latest real season repo (drop library-only / out-of-window teams)
seasonal = feat[feat.year.fillna(0) > 0]
latest = seasonal.sort_values("year").groupby("team", as_index=False).last()
latest = latest.merge(d8, on="team", how="left").merge(ci_team, on="team", how="left").fillna(0)
latest["year"] = latest.year.astype(int)
print(f"feature rows: {len(feat)}   teams scored (latest season): {len(latest)}")
latest.head(3)
""")

code(r"""
def lvl(*pairs):
    for cond, level in pairs:
        if cond: return level
    return 0

def score(r):
    # D1: ≥2 *IO interfaces is the IO-layer pattern (impls vary in name:
    # IOSim/IOReal, IOSparkMax/IOKraken, RealElevator/SimElevator, ...).
    D1 = lvl((r.servomotor>0 or r.io_adv>0, 4),
             (r.io_iface>=2, 3),
             (r.io_iface==1 or r.yagsl>0 or r.tuner>0, 2),
             (r.files>0, 1))
    D2 = lvl((r.graph>0 or r.jgrapht>0, 4), (r.coordinator>0, 3), (r.fsm>0, 2), (r.files>0, 1))
    D3 = lvl((r.io_adv>0, 4), (r.maple>0, 3),
             (r.wpilib_sim>0, 2), (r.sim_periodic>0, 1))
    D4 = lvl((r.runtocompletion>0 or (r.test_files>=10 and r.asserts>0), 4),
             (r.ci>0 and r.test_files>0, 3),
             (r.test_files>0 and (r.asserts>0 or r.test_ann>0), 2),
             (r.test_files>0 or r.test_ann>0, 1))
    D5 = lvl((r.faultreporter>0 or r.io_adv>0, 4), (r.advantagekit>0 and r.autolog>0, 3),
             (r.doglog>0 or r.logged>0 or r.epilogue>0, 2), (r.dashboard>0, 1))
    D6 = lvl((r.repulsor>0, 4), (r.choreo>0 or r.choreo_files>0, 3),
             (r.pathplanner>0 or r.pp_files>0, 2), (r.files>0, 1))
    D7 = lvl((r.robotstate>0, 4), (r.photon>0 and r.addvision>0, 3),
             (r.poseest>0 or r.addvision>0, 2), (r.limelight>0, 1))
    D8 = lvl((r.seasons>=4 and r.has_library and r.ci_any>0, 4),
             (r.ci_any>0 and r.has_library, 3),
             (r.contributors>=5 or r.has_library, 2), (r.contributors>=2, 1))
    return pd.Series({"D1":D1,"D2":D2,"D3":D3,"D4":D4,"D5":D5,"D6":D6,"D7":D7,"D8":D8})

scores = latest.join(latest.apply(score, axis=1))
scores["cand_total"] = scores[[f"D{i}" for i in range(1,9)]].sum(axis=1)
scores = scores.merge(q("SELECT team, name FROM teams"), on="team")
sheet = scores[["team","name","year"]+[f"D{i}" for i in range(1,9)]+["cand_total"]].sort_values("cand_total", ascending=False)
print("Candidate rubric scoresheet (top 15 of 63) — automated, confirm by reading:")
display(sheet.head(15).reset_index(drop=True))
""")

md(r"""
**Does the automated pass agree with the human scores?** Merge candidate totals with
the 24 hand-scored San Diego teams and correlate.
""")

code(r"""
hand = pd.read_csv(ROOT / "knowledge/survey/sd-frc-master.csv")
hand["team"] = hand.team.astype(int)
ren = {c: c+"_h" for c in [f"D{i}" for i in range(1,9)]+["Total"]}
hd = hand[["team"]+[f"D{i}" for i in range(1,9)]+["Total"]].rename(columns=ren)
val = scores.merge(hd, on="team")
print(f"{len(val)} teams in both. Spearman correlation, candidate vs hand:")
perdim = pd.DataFrame({
  "dimension":[f"D{i}" for i in range(1,9)]+["Total"],
  "spearman":[spearman(val[f"D{i}"], val[f"D{i}_h"]) for i in range(1,9)]
             +[spearman(val["cand_total"], val["Total_h"])]}).round(2)
display(perdim)

fig, ax = plt.subplots(figsize=(6,6))
ax.scatter(val.Total_h, val.cand_total, color=ACC, s=40)
for _,r in val.iterrows(): ax.annotate(int(r.team), (r.Total_h, r.cand_total), fontsize=7, alpha=.6)
ax.plot([0,32],[0,32],"--",color="#9ca3af"); ax.set_xlim(0,32); ax.set_ylim(0,32)
ax.set_xlabel("hand-scored Σ/32"); ax.set_ylabel("candidate Σ/32 (this DB)")
ax.set_title("Automated rubric vs. human scores"); plt.tight_layout(); plt.show()
""")

# ── Testing & simulation ───────────────────────────────────────────────────
md(r"""
## 5 · Testing & simulation — the rarest markers

D4 (testing) is the sharpest discriminator and barely correlates with winning — a pure
engineering-culture signal. The rubric's flag: **"architecture without verification"** —
a clean IO layer (D1≥3) with no tests (D4≤1).
""")

code(r"""
fig, ax = plt.subplots(1, 2, figsize=(13, 4.3))
n_tests = int((scores.test_files>0).sum())
ax[0].bar(["no tests","has src/test"], [len(scores)-n_tests, n_tests], color=["#9ca3af",ACC3])
ax[0].set_title(f"Teams with a test tree ({n_tests} of {len(scores)})"); ax[0].set_ylabel("teams")
sim = scores.D3.value_counts().sort_index()
ax[1].bar(sim.index.astype(str), sim.values, color=ACC)
ax[1].set_title("Candidate D3 (simulation) distribution"); ax[1].set_xlabel("level"); ax[1].set_ylabel("teams")
plt.tight_layout(); plt.show()

flag = scores[(scores.D1>=3) & (scores.D4<=1)][["team","name","D1","D4","D3","test_files"]]
print(f"⚑ Architecture-without-verification — IO layer but no tests ({len(flag)} teams):")
display(flag.sort_values("D1", ascending=False).reset_index(drop=True))
""")

# ── Code vs results ────────────────────────────────────────────────────────
md(r"""
## 6 · Does better code win?

Candidate scores joined to season-matched Statbotics EPA. The original 24-team hand-scored
study found Σ vs normalized EPA ≈ 0.55. Recomputed here on **candidate** scores across a
broader, more elite sample (55 teams incl. the national set), the link is weaker and the
per-dimension ranking shifts — a reminder that automated candidates ≠ confirmed scores, and
that the national elites have strong code *and* strong EPA, compressing the relationship.
""")

code(r"""
epa = q("SELECT team, year, norm_epa, winrate FROM epa WHERE status='ok'")
ce = scores.merge(epa, on=["team","year"], how="inner")
print(f"{len(ce)} teams with code+EPA in their latest season.")
rows=[]
for d in [f"D{i}" for i in range(1,9)]+["cand_total"]:
    rows.append({"dimension":d,
                 "rho_normEPA": spearman(ce[d], ce.norm_epa),
                 "rho_winrate": spearman(ce[d], ce.winrate)})
corr = pd.DataFrame(rows).set_index("dimension").round(2)
display(corr)

fig, ax = plt.subplots(1,2, figsize=(13,4.5))
ax[0].scatter(ce.cand_total, ce.norm_epa, color=ACC, s=35)
ax[0].set_xlabel("candidate Σ/32"); ax[0].set_ylabel("normalized EPA"); ax[0].set_title("Code sophistication vs. EPA")
corr["rho_normEPA"].drop("cand_total").plot(kind="barh", ax=ax[1], color=ACC3)
ax[1].set_title("Which dimensions track results (rho vs normEPA)"); ax[1].set_xlabel("Spearman rho")
plt.tight_layout(); plt.show()
""")

# ── Team profile ───────────────────────────────────────────────────────────
md(r"""
## 7 · Per-team profile

A reusable card: rubric vector, frameworks, and EPA for any team.
""")

code(r"""
def profile(team):
    r = scores[scores.team==team]
    if r.empty: return print("no data for", team)
    r = r.iloc[0]
    fw = [n for n,c in [("AdvantageKit",r.advantagekit),("PathPlanner",r.pathplanner),("Choreo",r.choreo),
          ("PhotonVision",r.photon),("maple-sim",r.maple),("DogLog",r.doglog),("YAGSL",r.yagsl)] if c>0]
    e = epa[epa.team==team].sort_values("year")
    print(f"-- {team} {r['name']}  (latest season {int(r.year)}) --")
    print("  rubric:", "  ".join(f"D{i}={r[f'D{i}']:g}" for i in range(1,9)), f"  total={r.cand_total:g}/32")
    print("  frameworks:", ", ".join(fw) or "-")
    print("  tests:", "yes" if r.test_files>0 else "no", "| sim:", "yes" if r.sim_periodic>0 else "no",
          "| IO interfaces:", int(r.io_iface))
    if not e.empty:
        print("  EPA:", "  ".join(f"{int(y)}:{int(n)}" for y,n in zip(e.year,e.norm_epa)))

for t in [254, 1155, 4738, 3128]:
    profile(t); print()
""")

md(r"""
---
*Generated by `scripts/build_notebook.py` from `data/code-index.duckdb`
(`python3 main.py index-db`). Candidate rubric scores are automated signals — confirm
by reading the cited files before reporting a team's score.*
""")


# ───────────────────────────────────────────────────────────────────────────
def build() -> None:
    nb = new_notebook()
    nb.cells = [new_markdown_cell(s) if k == "md" else new_code_cell(s) for k, s in CELLS]
    nb.metadata.kernelspec = {"name": "python3", "display_name": "Python 3", "language": "python"}
    print(f"executing {len(nb.cells)} cells against data/code-index.duckdb ...")
    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
    ep.preprocess(nb, {"metadata": {"path": str(ROOT)}})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
