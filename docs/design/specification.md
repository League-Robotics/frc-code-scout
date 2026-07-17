# FRC Code Scout — Specification

This describes the system as it currently exists. It is not a proposal for new work.

## What the repo contains

- **`knowledge/`** — the embedded, read-only research base: the rubric
  (`knowledge/rubric/rubric.md`), the national corpus analysis, the elite
  build-spec architecture (`knowledge/build-spec/`), the San Diego regional
  survey data, and worked examples.
- **`data/`** — team manifests (version-controlled seed list of team/repo
  identifiers) plus downloaded repos and build indexes (gitignored,
  reproducible from the manifest).
- **`scripts/`** — `clone_corpus`, `discover_repos`, `build_index`, `score_rubric`,
  and prediction/agent-scoring tooling.
- **`rules/`** — ast-grep rule files implementing each rubric dimension (D1–D8).
- **`.claude/skills/`** and **`.claude/agents/`** — the agent-facing capabilities
  described below, plus the CLASI SE process scaffolding used to plan and execute
  work on this repo itself.
- **`site/` / `docs/elite-arch`** — the published Hugo book generated from
  `knowledge/`.

## Function 1: Score a team's code

Given a team identifier (and optionally their GitHub org), the system can:
- discover and download their repo(s) (single season, or with history for a
  multi-year trajectory),
- run a mechanical ast-grep/filesystem pass to produce *candidate* D1–D8 levels,
- require an agent to confirm each candidate by opening the cited evidence files
  ("score what's used, not what's present" — the non-negotiable rule; confirmed
  scoring roughly doubles predictive validity against competition EPA versus the
  mechanical pass alone),
- compare the team to the San Diego survey peer set,
- write a benchmarked report with prioritized next steps mapped to the build-spec.

Supporting capability: re-download and re-index the *entire* tracked corpus, or add
newly discovered teams, so cross-team questions can be asked at any time.

## Function 2: Build the elite architecture into a robot project

Given a WPILib robot project (new or existing), the system can:
- scaffold the three structural seams — a per-subsystem IO layer, `RobotState`,
  and `Superstructure` — plus a REAL/SIM/REPLAY run mode and a swerve `Drive`,
- stamp out one mechanism at a time (elevator, arm, shooter, etc.) as a full IO
  quartet (`XxxIO` + inputs, `XxxIO<device>`, `XxxIOSim`, the subsystem, constants)
  with a sim-backed unit test,
- wire in the cross-cutting practices: unit testing, structured logging
  (AdvantageKit-style with replay), and physics simulation,
- audit an existing project against the rubric and the build-spec and name the
  single highest-leverage next step.

The invariant enforced throughout: a vendor type (`com.ctre`, `com.revrobotics`,
`org.photonvision`) may appear only inside an `XxxIO<device>`/`XxxIOSim` file —
never in a subsystem, command, `RobotState`, or `Superstructure`.

## Function 3: Publish the book

The `knowledge/` content is rendered into a public Hugo site (five parts: Rubric,
Corpus Analysis, Build Spec, Survey, Examples) so the rubric and architecture are
usable outside the agent workflow.

## Non-goals

- This spec does not propose new features. Future sprints define incremental
  changes against this baseline via their own architecture-update documents.
- No UI/dashboard beyond the generated static site.

## Constraints

- Downloads must target a plain local disk (`SCOUT_DATA` override) — cloud-synced
  or network-mounted folders break git's `.git` handling.
- Corpus scoring for the model-confirmation tier should use Sonnet, not Opus or
  Haiku, per the model-fidelity pilot in `tests/model-fidelity/`.
