# FRC Code Scout (Claude Code entry point)

Read **`AGENTS.md`** for the full instruction set — it is the canonical, tool-agnostic
guide and applies here verbatim.

This repo does two things: it **scores** FRC/FTC team code against an 8-dimension rubric, and it
**builds** that architecture into new robot projects. Skills live in `.claude/skills/` and
subagents in `.claude/agents/`.

**Analyze a team's code:**
- **analyze-team** — score a team and write a benchmarked report (e.g. "score the Patribots").
- **reproduce-corpus** — re-download, index, and query all teams' code.
- Supporting: **score-rubric** (one-repo candidate pass), **index-code** (ast-grep / cocoindex),
  **update-corpus** (seasonal self-refresh).

**Build a robot the elite way** (scaffold the architecture from `knowledge/build-spec/`):
- **scaffold-robot** — bootstrap the three seams (IO layer, RobotState, Superstructure) + run-mode.
- **add-subsystem** — generate one mechanism's IO quartet + a sim-backed test for any archetype.
- **setup-testing / setup-logging / setup-simulation** — wire the cross-cutting practices.
- **audit-architecture** — score the *current* project against the rubric + build-spec.

Golden rules: when scoring, **score what's USED, not present** — confirm every candidate by opening
the cited files. When building, **never let a vendor type (`com.ctre`/`com.revrobotics`/
`org.photonvision`) appear above the IO line.** The rubric is `knowledge/rubric/rubric.md`; the
architecture book is `knowledge/build-spec/`.

Set `export SCOUT_DATA=/local/path` before downloading if this repo lives on a
cloud-synced or mounted folder (git `.git` handling fails on synced drives).
