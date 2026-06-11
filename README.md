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

## Tools

- [ast-grep](https://ast-grep.github.io/) — tree-sitter AST structural search (required).
- [cocoindex](https://cocoindex.io/) — optional semantic "ask the code" index.

## Provenance

Built from the San Diego FIRST Robotics inventory project. Worked example:
`knowledge/examples/patribots-four-year-scoring.md`. Method: `knowledge/examples/methodology.md`.
# frc-code-scout
