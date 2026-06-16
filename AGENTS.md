# FRC Code Scout — Agent Guide

This repository is a portable analysis environment for scoring FRC (and FTC) team
software against an 8-dimension **code-sophistication rubric**, plus the research
corpus that the rubric was derived from. It is designed to be driven by an AI coding
agent — Claude Code, Codex, Cursor, or any agent that reads `AGENTS.md`.

This file is the **canonical, tool-agnostic instruction set.** Tool-specific entry
points (`CLAUDE.md`, `.cursor/rules/`, `.claude/skills/`) all point back here.

---

## What you can do here

Two primary jobs:

1. **Analyze one team** — score a team's repo(s) against the rubric, compare them to
   the 24-team San Diego survey, and write a report with prioritized next steps.
   (Worked example: `knowledge/examples/patribots-four-year-scoring.md`.)
2. **Reproduce / extend the corpus** — re-download every team's code, discover repos
   for teams not yet tracked, index the code for fast structural search, and ask
   questions across the whole corpus.

## The most important rule

**Score what's *used*, not what's *present*.** The scripts do a fast mechanical pass
(ast-grep AST matches + filesystem checks) and emit *candidate* levels. You must
confirm every candidate by opening the cited files before reporting a score. A Choreo
vendordep with no trajectories is not Choreo adoption; an empty `src/test` folder is
not testing. This is non-negotiable and is what separates this tool from a linter.

---

## Layout

```
knowledge/        Embedded research (read-only reference)
  rubric/         THE RUBRIC — read this first for any scoring task
  corpus-analysis/  National 37-team FRC survey, IO-layer/Strategy deep dive, ladder
  build-spec/     Elite-track architecture spec (use for recommendations)
  survey/         San Diego results: scores, correlations, final report, inventory
  examples/       Worked outputs (Patribots 4-year report, methodology, sample score)
data/
  manifests/      team_id|name|github_owner|repos  (version-controlled, the seed list)
  repos/          downloaded code        (gitignored — reproducible)
  index/          per-repo symbol + rubric-hit JSON (gitignored)
rules/            ast-grep rule files implementing rubric dimensions D1..D8
scripts/          clone_corpus · discover_repos · build_index · score_rubric
sgconfig.yml      ast-grep project config (points at rules/)
```

## Setup (once)

- **ast-grep** (required, structural AST search): `npm i -g @ast-grep/cli`
  or `pip install ast-grep-cli` or `brew install ast-grep` or `cargo install ast-grep`.
  `scripts/build_index.sh` will attempt this automatically.
- **cocoindex** (optional, semantic "ask the code" search): `pip install cocoindex`.
- **git**, **python3**, and **bash** must be on PATH.
- **Downloads must target a plain local disk.** Set `export SCOUT_DATA=/some/local/path`
  if this repo lives on a cloud-synced or network-mounted folder — git's `.git`
  handling and stripping fail on synced drives.

---

## Workflow A — Analyze one team

1. Read `knowledge/rubric/rubric.md` in full. It defines D1–D8, the anchors, and the
   grep cheat-sheet.
2. Make sure the team is in `data/manifests/frc-teams.tsv`. If not, discover it:
   `scripts/discover_repos.sh --owner THEIR_GH_ORG --team-id 1234 --name their-name --append frc`
3. Download their code. For a single-season score, shallow is fine; **for a multi-year
   trajectory you need history** — use `--with-git`:
   `scripts/clone_corpus.sh --team 1234 --with-git`
4. Index it: `scripts/build_index.sh --team 1234`
5. For each season repo, get candidate levels: `scripts/score_rubric.sh --repo PATH`
6. **Confirm every candidate by opening the cited evidence files.** Adjust levels.
   Use `ast-grep run -p 'PATTERN' PATH` and read the symbol map in `data/index/...`.
7. If `--with-git`, read the commit history for the trajectory: when did the IO layer /
   AdvantageKit / Superstructure land? In-season or offseason? (See the Patribots
   example — the commit story is often the real finding.)
8. Compare to peers using `knowledge/survey/sd-frc-master.csv` (per-team D1–D8 vectors)
   and `knowledge/survey/sd-frc-correlations.csv` (which dimensions track results).
9. Write the report from `templates/team-report.md`. Recommendations should map gaps to
   the seams in `knowledge/build-spec/elite-architecture.md`.

## Workflow B — Reproduce / extend the corpus

1. `scripts/clone_corpus.sh` (no `--team`) downloads everything in the manifest.
   Flags: `--with-git` keep history · `--keep-logs` keep replay logs (`.wpilog` etc.,
   useful for log-replay analysis) · `--keep-media` keep CAD/video · `--budget N`
   time-box and resume · `--league ftc` for the FTC manifest.
2. Find teams you don't have yet: `scripts/discover_repos.sh --search "San Diego FRC"`
   then `--owner <org> --append frc` to add them.
3. `scripts/build_index.sh` indexes everything (add `--semantic` for cocoindex).
4. Ask questions across the corpus with ast-grep, e.g.:
   - Who runs a Superstructure FSM? `ast-grep scan --config sgconfig.yml data/repos --json | python3 -c "..."` filtered to `d2-superstructure-class`.
   - Which teams test? `ast-grep run -l java -p '@Test' data/repos`
   - Every IO interface across the corpus: `ast-grep run -l java -p 'interface $N' data/repos | grep IO`
5. To re-run the full San Diego scoring, score each team's latest real season repo and
   rebuild a master CSV in the shape of `knowledge/survey/sd-frc-master.csv`.

## Workflow C — Build a robot the elite way

The same architecture the rubric measures can be *built*, not just scored. The book is
`knowledge/build-spec/` (the spec) → `subsystems/00-08` (per-archetype guides) → `logging.md` /
`testing.md` / `simulation.md` (practices). The skills scaffold it:

1. **`scaffold-robot`** — lay the three seams (per-subsystem IO layer, `RobotState`,
   `Superstructure`) + a REAL/SIM/REPLAY run mode + a swerve `Drive`. Build the seams first;
   everything else attaches to them.
2. **`add-subsystem`** — given an archetype (linear / rotational / velocity / roller / vision) and a
   name, stamp out the full IO quartet (`XxxIO`+inputs, `XxxIO<device>`, `XxxIOSim`, the subsystem,
   constants) **plus a sim-backed unit test**. Skeleton templates ship beside the skill.
3. **`setup-testing` / `setup-logging` / `setup-simulation`** — wire the practices.
4. **`audit-architecture`** — turn the rubric inward: score the *current* project, flag missing
   seams and vendor leaks, and name the one highest-leverage next step.

**The build golden rule:** a vendor type (`com.ctre`, `com.revrobotics`, `org.photonvision`) appears
**only** inside an `XxxIO<device>`/`XxxIOSim` file — never in a subsystem, command, `RobotState`, or
`Superstructure`. That confinement is what makes the code simulatable, testable, and portable.

## Keeping the tool current (self-update)

The `update-corpus` skill re-pulls every tracked repo (so scores reflect current code),
re-discovers new repos per team, and flags teams whose newest season repo changed. Run
it at the start of a new season. The manifest is the source of truth; downloaded code is
always reproducible from it.

---

## Scoring quick reference (D1–D8, each 0–4)

D1 Hardware decoupling · D2 Coordination · D3 Simulation · D4 Testing · D5 Logging ·
D6 Auto/Path · D7 Vision/Localization · D8 Sustainability. Half-steps allowed. Report
the **vector and the profile shape**, not just the sum — see the rubric's "common
shapes" section. D4 (testing) is the rarest, most discriminating marker; most teams
score 0.
