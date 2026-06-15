# FRC Code Scout

A portable environment for scoring FRC (and FTC) team **software** against an
8-dimension code-sophistication rubric — and the research corpus that the rubric was
built from. Point an AI coding agent (Claude Code, Codex, Cursor, …) at this repo and ask
it to analyze a team or rebuild the dataset.

## What's in here

- **The rubric** (`knowledge/rubric/rubric.md`) — eight 0–4 dimensions (architecture,
  coordination, simulation, testing, logging, autonomous, vision, sustainability), with
  anchored indicators and a structural-search cheat-sheet.
- **The research corpus** (`knowledge/`) — the national 37-team FRC survey, the IO-layer /
  Strategy-pattern deep dive, the novice→elite progression ladder, the elite-architecture
  build spec, and the full 24-team San Diego survey with competition-result correlations.
- **A working pipeline** (`scripts/` + `rules/` + `sgconfig.yml`) — download team repos,
  strip the bulk, index with **ast-grep**, and produce candidate rubric scores with
  file-level evidence.
- **Agent wiring** — `AGENTS.md` (canonical), `CLAUDE.md`, `.claude/skills` + `.claude/agents`,
  `.cursor/rules`, and a `.claude-plugin` manifest so it installs as a Claude Code plugin.

## Quick start

```bash
# 0. one-time: install the structural search engine
npm i -g @ast-grep/cli      # or: pip install ast-grep-cli / brew install ast-grep

# downloads need real disk (not a synced folder):
export SCOUT_DATA=/path/on/local/disk

# 1. analyze ONE team (e.g. Patribots, with history for a trajectory)
scripts/clone_corpus.sh  --team 4738 --with-git
scripts/build_index.sh   --team 4738
scripts/score_rubric.sh  --repo "$SCOUT_DATA/repos/frc/4738-patribots/Reefscape2025"
#   -> candidate D1-D8 levels + evidence. Then CONFIRM by opening the cited files,
#      and write the report from templates/team-report.md.

# 2. rebuild / extend the WHOLE corpus
scripts/clone_corpus.sh                 # everything in the manifest (shallow, cleaned)
scripts/discover_repos.sh --search "San Diego FRC"   # find teams you don't have
scripts/build_index.sh                  # index it all (add --semantic for cocoindex)
ast-grep run -l java -p '@Test' "$SCOUT_DATA/repos"   # ask the corpus a question
```

## The one rule that matters

**Score what's *used*, not what's *present*.** The scripts produce *candidates*; a human or
agent confirms each by reading the cited code. That's the difference between this and a
linter — see `AGENTS.md`.

## Download options

`clone_corpus.sh` flags: `--with-git` (keep history, needed for trajectory analysis) ·
`--keep-logs` (keep `.wpilog/.hoot/.rlog` replay logs) · `--keep-media` (keep CAD/video) ·
`--budget N` (time-box and resume) · `--team ID` · `--league ftc`. Default strips `.git`,
media, CAD, large binaries, and logs to keep the corpus small and code-only.

## Multi-year corpus + EPA dataset (`scout/`)

`scout/` is a zero-dependency (stdlib-only) Python program that builds a richer,
self-describing corpus across **two team populations** — the 37 national teams from the
survey (`data/manifests/national-frc-teams.tsv`) and the San Diego teams
(`data/manifests/frc-teams.tsv`), de-duplicated by team number. For every team, across the
**2022–2026** seasons, it:

- discovers each season's repos on GitHub (curated manifest repos ∪ in-window-season repos);
- clones each with full history, then **extracts the commit log as data** — per check-in:
  date, author, files changed, and change size (insertions/deletions) — into a per-repo
  `history.json`, and **strips `.git`** afterward (history, not blobs);
- keeps the working-tree source but **suppresses** large/binary/media/doc files to 0-byte
  `*.sup` stubs (e.g. `clip.mov` → `clip.mov.sup`);
- looks up **Statbotics EPA** (`api.statbotics.io/v3`) per team per year;
- writes a per-team `manifest.json` (every GitHub URL visited), a committed
  `data/master-dataset.json`, and a human-readable `data/corpus-inventory.md`.

```bash
export GITHUB_TOKEN=...            # raises GitHub API limit to 5000/hr
python3 main.py build             # full corpus -> ./frc_team_repos/<num>-<name>/<year>/<repo>/
python3 main.py build --team 4738 # one team   (resumable; --keep-git, --budget N, --no-clone)
python3 main.py list-teams        # merged, de-duplicated team list
python3 main.py discover --team 6328   # show the repo plan (no clone)
python3 main.py epa --team 254         # Statbotics EPA across the season window
```

The corpus root defaults to `./frc_team_repos` (a symlink to local disk); override with
`--output-root` or `$SCOUT_DATA`. The build is resumable: GitHub/Statbotics responses are
cached under `data/cache/` and already-cloned repos are skipped.

## Tools

- [ast-grep](https://ast-grep.github.io/) — tree-sitter AST structural search (required).
- [cocoindex](https://cocoindex.io/) — optional semantic "ask the code" index.

## Provenance

Built from the San Diego FIRST Robotics inventory project. Worked example:
`knowledge/examples/patribots-four-year-scoring.md`. Method: `knowledge/examples/methodology.md`.
# frc-code-scout
