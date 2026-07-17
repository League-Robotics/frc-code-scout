# FRC Code Scout — Use Cases

## UC-001: Score a single team's code
- **Actor**: Mentor/analyst (via AI agent)
- **Preconditions**: Team is in, or can be added to, `data/manifests/*.tsv`.
- **Main flow**: Agent discovers/downloads the team's repo(s), runs the mechanical
  ast-grep pass to get candidate D1–D8 levels, opens the cited evidence files to
  confirm each candidate, compares to the survey peer set, writes a benchmarked
  report with prioritized next steps.
- **Postconditions**: A team report exists with confirmed D1–D8 scores and
  recommendations mapped to the build-spec.
- **Error flows**: Team not found on GitHub — report and stop, do not guess a repo.
  Repo has no matching evidence for a candidate hit — score it down, do not accept
  the mechanical candidate at face value.

## UC-002: Reproduce or extend the full corpus
- **Actor**: Analyst / self-update process
- **Preconditions**: Manifest of tracked teams exists.
- **Main flow**: Re-download every tracked team's repo(s), discover new teams'
  repos and add them to the manifest, rebuild the per-repo search index.
- **Postconditions**: `data/repos/` and `data/index/` reflect the current state of
  every tracked team; new teams are queryable.
- **Error flows**: Repo lives on a cloud-synced/mounted drive — instruct the user
  to set `SCOUT_DATA` to a local path before downloading.

## UC-003: Ask a cross-team question
- **Actor**: Analyst
- **Preconditions**: Corpus is downloaded and indexed (UC-002).
- **Main flow**: Run an ast-grep query (or semantic query, if cocoindex is
  enabled) across `data/repos` to answer a structural question, e.g. "which teams
  run a Superstructure FSM" or "which teams have unit tests."
- **Postconditions**: Answer returned with supporting file citations.
- **Error flows**: Index missing or stale — rebuild via UC-002 before querying.

## UC-004: Scaffold a new robot project on the elite architecture
- **Actor**: Team mentor/student (via AI agent)
- **Preconditions**: A WPILib project exists (new or early-stage).
- **Main flow**: Agent lays the three seams (per-subsystem IO layer, `RobotState`,
  `Superstructure`), adds a REAL/SIM/REPLAY run mode, and a swerve `Drive` with
  `ModuleIO`/`GyroIO`.
- **Postconditions**: Project has the structural seams in place; subsystems can be
  added without rewrites.
- **Error flows**: Project already has incompatible structure — flag the conflict
  rather than silently overwriting it.

## UC-005: Add one subsystem to a scaffolded project
- **Actor**: Team mentor/student
- **Preconditions**: Project already has the three seams (UC-004).
- **Main flow**: Given an archetype (linear/rotational/velocity/roller/vision) and
  a name, generate the full IO quartet (`XxxIO`+inputs, `XxxIO<device>`,
  `XxxIOSim`, the subsystem, constants) plus a sim-backed unit test.
- **Postconditions**: New subsystem compiles, runs in sim, and is covered by a
  test — with no vendor type appearing outside its `XxxIO<device>`/`XxxIOSim`
  files.
- **Error flows**: Requested archetype has no matching template — report which
  archetypes are supported instead of guessing.

## UC-006: Audit an existing project's architecture
- **Actor**: Team mentor/student
- **Preconditions**: A robot project exists (any maturity level).
- **Main flow**: Score the current project against the same D1–D8 rubric and the
  build-spec; flag missing seams and any vendor-type leaks above the IO line; name
  the single highest-leverage next step.
- **Postconditions**: Audit report produced with a concrete next action.
- **Error flows**: Project has no discernible structure to score — report D1 as
  the starting gap rather than failing outright.

## UC-007: Publish/maintain the book site
- **Actor**: Maintainer
- **Preconditions**: `knowledge/` content is current.
- **Main flow**: Render `knowledge/` into the Hugo site (`site/` /
  `docs/elite-arch`) covering the five parts (Rubric, Corpus Analysis, Build Spec,
  Survey, Examples); publish.
- **Postconditions**: Public site reflects the current `knowledge/` content.
- **Error flows**: Rendered diagrams or links go stale relative to source —
  re-render before publishing (see `docs-build-architecture` project notes).
