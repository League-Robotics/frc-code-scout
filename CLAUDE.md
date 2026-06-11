# FRC Code Scout (Claude Code entry point)

Read **`AGENTS.md`** for the full instruction set — it is the canonical, tool-agnostic
guide and applies here verbatim.

This repo scores FRC/FTC team code against an 8-dimension rubric and bundles the research
corpus behind it. Skills live in `.claude/skills/` and subagents in `.claude/agents/`.

Two main skills:
- **analyze-team** — score a team and write a benchmarked report (e.g. "score the Patribots").
- **reproduce-corpus** — re-download, index, and query all teams' code.

Supporting skills: **score-rubric** (one-repo candidate pass), **index-code** (ast-grep /
cocoindex indexing), **update-corpus** (seasonal self-refresh).

Golden rule: **score what's USED, not present** — confirm every ast-grep/filesystem
candidate by opening the cited files. The rubric is `knowledge/rubric/rubric.md`.

Set `export SCOUT_DATA=/local/path` before downloading if this repo lives on a
cloud-synced or mounted folder (git `.git` handling fails on synced drives).
