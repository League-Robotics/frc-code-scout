---
title: 33. The rubric in full
weight: 33
---


**This is the complete, authoritative rubric — eight dimensions, each scored 0–4 against anchored, observable indicators, with half-steps allowed.** The companion chapter [how to read the rubric](../appendices/how-we-developed-this/02-the-rubric.md) explains why it is shaped this way and how to use it; this page carries every anchor, every caution, and the grep/AST cheat-sheet in full, so it can be scored from directly.

---

## Why dimensions, not a single ladder score

The [maturity ladder](../appendices/how-we-developed-this/03-the-maturity-ladder.md) is right about *sequence within a dimension* — nobody reaches unit tests without an IO layer, because the IO layer is what makes subsystems testable. But real teams adopt unevenly *across* dimensions: a team can have a clean IO layer and zero tests, or AdvantageKit logging bolted onto spaghetti coordination, or Choreo trajectories driven by dead-reckoned odometry. A single ladder score hides exactly the gaps that matter most — "you've built the IO layer, tests are one step away, and you're not taking it."

So: score each dimension independently, report the vector, and read the *shape* of the profile, not the sum. One revision to the ladder this implies — the teaching order bundles "IO layer + simulation + lightweight logging" as one leap and "FSM + tests + replay" as another; in the wild these decompose. That bundling is the right *teaching* order but the wrong *measurement* instrument, so the rubric splits them.

---

## Scoring rules

- **Unit** — each team's most recent real competition-season repo (2025 or 2026; not templates, training repos, or off-season toys). Record the repo name and season on the scoresheet.
- **Adjacent repos count for one dimension only** — separate team-library repos (`SuperCORE`, `WarlordsLib`, `3128-common`, `NOMADBase`) and training repos count toward **D8 (Sustainability)** but not toward the code dimensions, which are scored from the season repo alone.
- **Score what's used, not what's present.** A Choreo vendordep JSON with no `.traj` files and no Choreo imports is not Choreo adoption. An empty `src/test` folder is not testing. Confirm every indicator by opening at least one file — see [Part I ch. 3 — the IO seam](../part-1/03-the-io-seam.md) for why the seam is the load-bearing structure to confirm.
- **Half-steps are allowed** (e.g., 2.5) when a team sits clearly between anchors. Don't agonize.
- **Known blind spot** — repos are shallow clones with `.git` stripped, so commit history, PRs, and contributor counts are unobservable. D8 is scored from artifacts only and should be treated as a floor, not a ceiling.
- **Language note** — anchors are written in Java/WPILib terms. Kotlin (6695) and Python/RobotPy teams hit the same anchors with different syntax: MagicBot's framework FSM counts at D2 level 2, its component injection counts at D1 level 2.

---

## Corpus prevalence (measured)

From the tree-sitter → DuckDB index of 55 season repos. Use these to calibrate: a marker present in 3 teams is a ceiling signal; one present in 45 is table stakes. Confirm by reading regardless.

| Marker | Teams (of 55) | Calibration note |
|---|---|---|
| `commands/` dir · `Constants` · `subsystems/` dir | 54 · 54 · 53 | universal — no signal |
| `addVisionMeasurement` call | 50 | vision/pose-est is assumed (D7 ≥ 2 is the floor, not the ceiling) |
| PhotonVision import | 42 | |
| `*PoseEstimator` · `*RobotState` class | 36 · 26 | pose-est ≫ centralized world-model (D7 L2 vs L4 split is real) |
| `util/` dir · `lib/` dir | 36 · 26 | lib/robot split (D8) in ~half |
| `*IO` interface · `*Inputs` struct | 24 · 26 | **IO seam ≈ 44%; every IO team has an Inputs struct (0 exceptions)** |
| `*IOSim` impl · `@AutoLog` | 19 · 19 | |
| `generated/` dir (CTRE Tuner swerve) | 19 | a real structural element worth recognizing |
| `Superstructure` class | 22 | **the dominant coordinator name** |
| device-named HW impl (`*IOTalonFX` 14 / `*IOPigeon2` 12 / `*IOLimelight` 12 / `*IOSparkMax` 7) | — | **this is how hardware impls are named** |
| generic `*StateMachine` | 12 | second coordination marker |
| `*IOReal` | **5** | ⚠ rare — do **not** grep for this to find an IO layer |
| `jgrapht` · `RobotManager` · `WantedState` enum · `*IONull` · replay IO variant · BehaviorTree | 3 · 2 · 2 · ~1 · 1 · 1 | true ceiling markers; a hit is a strong D2/D5 signal |
| vendor type (`com.ctre`/`com.revrobotics`) imported *above* the IO line | 22 of 24 IO teams | clean vendor confinement is aspirational, not the norm — **judge it by reading, not by filename**: some teams confine vendor types in wrapper classes *not* named `*IO` (e.g. 4738's `Kraken.java`/`SafeSpark.java`), which a `*IO`-name heuristic wrongly flags as a leak |

Most-common subsystems (by `subsystems/<dir>`): **vision · intake · drive · shooter · climber · elevator**, then arm · LEDs · indexer · turret. Manipulator is rare; subsystem names are game-dependent — score the IO/coordination *structure*, not the mechanism roster.

---

## What predicts competition results — and why you must read the code

Measured 2026 against Statbotics EPA, leave-one-**team**-out cross-validated over 232 team-years / 55 teams, cluster-bootstrap CIs. Three results should shape how you use this rubric:

1. **Confirming use, not presence, roughly doubles the rubric's predictive validity.** On the same 55 teams, the **agent-confirmed** D1–D8 (a model that opened the files) predicts EPA at Spearman **ρ ≈ 0.53**; the **mechanical candidate** pass (grep/SQL hits, scored as presence) reaches only **ρ ≈ 0.29**. The paired difference is significant (95% CI `[0.04, 0.44]`). This is the empirical case for the golden rule — the cheap pass is a lead sheet, not a score.

2. **Most of what predicts EPA from "code" is just size and program age — not engineering quality.** A model of ~50 raw code features hits ρ ≈ 0.58, but **codebase size + program maturity alone scores ≈ 0.60**, while the *sophistication* features (the rubric's structural patterns, size removed) score ≈ 0.38, and a within-team (fixed-effects) view collapses to ≈ 0.05. Bigger, older, better-resourced programs have both more code and better results. Do not read a high raw correlation as "good code wins" — and do not reward sheer volume.

3. **The mechanical pass is trustworthy on some dimensions and not others.** Agreement (quadratic-κ) between the mechanical candidate and the agent-confirmed level:

   | Dimension | κ (mechanical vs confirmed) | Trust the grep? |
   |---|---|---|
   | D4 Testing | 0.86 | yes — `src/test` + asserts is unambiguous |
   | D1 Architecture | 0.82 | yes — `*IO` interfaces are concrete |
   | D3 Simulation | 0.81 | yes |
   | D2 Coordination · D5 Logging | 0.74 | mostly — confirm the coordinator is real, logging covers all subsystems |
   | **D6 Auto/Path · D7 Vision** | **0.60** | **no — confirm by reading** (files present ≠ trajectories driven / vision fused) |
   | **D8 Sustainability** | **0.57** | **no — read the README/CI/library; history is shallow** |

   Spend your reading budget where κ is low: **D6, D7, D8** are where "present" most diverges from "used." Equal-weighting the eight dimensions is fine — an EPA-optimal re-weighting was not distinguishable from equal weight on this sample, so don't over-engineer the sum.

---

## D1 — Hardware decoupling (architecture)

*The ladder's spine — how far has the team pushed the boundary between subsystem logic and physical devices?*

| Level | Anchor | Observable indicators |
|---|---|---|
| 0 | Everything in `Robot.java` / timed-robot blob | No subsystem classes, or one giant file; motor objects and game logic interleaved |
| 1 | Command-based baseline | `SubsystemBase` subclasses own motors directly; commands call subsystem methods; a `Constants` file exists |
| 2 | Partial or vendored abstraction | Vendored swerve abstraction (YAGSL, CTRE swerve generator) but mechanisms still hardware-welded; or IO interfaces on one or two subsystems only |
| 3 | IO layer as the default | Per-subsystem `*IO` interfaces with at least Real + Sim implementations across most mechanisms; selection in one place (switch/factory) |
| 4 | Generalized / library-grade | Generic parameterized bases (254-style `ServoMotorSubsystem`), null-object IO variants, or replay IO variants; the abstraction is reused, not repeated |

**Grep:** `interface .*IO` (the spine), plus its implementations — `*IOSim*` (the sim impl, 19 teams) and a **hardware impl named by device**: `*IOTalonFX*` / `*IOKraken*` / `*IOSparkMax*` / `*IOSpark*` / `*IOPigeon2*` / `*IONavX*` / `*IOLimelight*` / `*IOPhoton*`. **Do not rely on `*IOReal*`** — only ~5 teams use that name; the robust signal is *an `interface *IO` with ≥2 implementations, one of them `*IOSim`*. Also `@AutoLog`, YAGSL config dirs (`src/main/deploy/swerve`), `TunerConstants` (CTRE generator). At L4: a generic base (`MotorIO`/`ServoMotorSubsystem`) reused across mechanisms — the `*IONull*` null-object variant is real but near-absent in the corpus (~1 team), so don't require it.

**Distinguish at level 3:** an IO *directory* of concrete hardware wrappers (the 2056 case) is not an IO *layer* — there must be an interface with swappable implementations. Check for an actual `interface` and at least two implementations.

---

## D2 — Coordination & decision logic

*How does the robot decide what to do and keep mechanisms from fighting?*

| Level | Anchor | Observable indicators |
|---|---|---|
| 0 | Imperative teleop | Joystick values mapped straight to motor outputs in a periodic method; no command composition |
| 1 | Command composition | Sequential/parallel command groups; button bindings in `RobotContainer`; autos as command sequences |
| 2 | Explicit state machines | Wanted/current enums per subsystem (2910 style) or a centralized `RobotManager` FSM (581 style); a transition function owns state changes |
| 3 | Superstructure coordination | A coordinator object fans robot-wide goals out to subsystems; intent (requested state) is separated from execution; kinematic safety handled deliberately (motion planner or guarded transitions) |
| 4 | Search/graph-based or beyond | State graph with pathfinding (JGraphT / A* over states), behavior tree runtime, or equivalent — transition logic as data, not code |

**Grep:** `Superstructure` (the dominant coordinator — 22 teams; check it's a real goal-fanout, not a holder), generic `*StateMachine` (12 teams). Rarer variants, each a strong signal when present but few teams: `enum WantedState`/`SystemState` (2910 style — 2 teams), `RobotManager` (581/3128 centralized FSM — 2 teams), `handleStateTransitions`, `jgrapht` (3), `AStarSolver`, `BehaviorTree` (1). Don't weight `WantedState`/`RobotManager` as the default — they're niche; the common path is a `Superstructure` (level 3) optionally backed by a `*StateMachine`. A newer L3 marker worth recognizing: a **request-based API** — a `Goal`/`SuperstructureRequest` enum or sealed type plus a `requestGoal(...)`/`request(...)` method (often returning a `Command`) and a `handleStateTransitions`-style guard — which makes intent-vs-execution explicit.

**Caution:** a class *named* Superstructure that just holds references is level 1 wearing a level 3 name. Look for an actual goal-request API and transition logic.

---

## D3 — Simulation

*Can the code run, and surprise you, without the robot?*

| Level | Anchor | Observable indicators |
|---|---|---|
| 0 | None | No `simulationPeriodic`, no sim classes |
| 1 | Token sim | `simulationPeriodic` stubs or a sim GUI run that echoes setpoints; no physics |
| 2 | Mechanism physics sim | WPILib physics classes (`ElevatorSim`, `SingleJointedArmSim`, `FlywheelSim`, `DCMotorSim`) wired into IO sim implementations for the main mechanisms |
| 3 | Whole-robot sim workflow | Sim covers drivetrain + mechanisms + (ideally) vision; maple-sim or equivalent dynamics; evidence the team develops in sim (sim-specific configs, sim auto-testing mode) |
| 4 | Sim/replay as primary verification | Deterministic re-simulation or log replay of real matches treated as a workflow (replay IO variants, ideal-sim variants, 4481 style) |

**Grep:** `simulationPeriodic`, `ElevatorSim|SingleJointedArmSim|FlywheelSim|DCMotorSim|SwerveDriveSim`, `maple-sim` / `org.ironmaple`, `*IOReplay*`, `IdealSim`.

---

## D4 — Testing & verification

*The IO layer's deferred dividend. Almost no team collects it — the sharpest discriminator in the corpus.*

| Level | Anchor | Observable indicators |
|---|---|---|
| 0 | None | No `src/test`, or only the GradleRIO boilerplate test |
| 1 | Token tests | A handful of trivial tests (constants, math utilities); not run anywhere |
| 2 | Real unit tests | Tests that construct sim-backed subsystems and assert on behavior; meaningful coverage of at least a few mechanisms |
| 3 | Tests in CI | `.github/workflows` runs `gradle test` (not just build) on push/PR; tests gate merges |
| 4 | Command-level verification | Tests run actual commands to completion in simulation and assert on resulting state (SciBorgs `runToCompletion` style); broad suite (10+ test files) |

**Grep:** `src/test/java` tree, `@Test`, `assertEquals`, `.github/workflows/*.yml` containing `test`, `runToCompletion`, `CommandTestBase`.

**Note the asymmetry with D3:** physics sim without tests (common) scores D3 high / D4 low. That gap is the single most actionable finding for a team — flag it in notes.

---

## D5 — Logging, telemetry & diagnostics

*"When the robot misbehaves on the field, how do we know why?"*

| Level | Anchor | Observable indicators |
|---|---|---|
| 0 | Prints | `System.out.println` debugging or nothing |
| 1 | Dashboard values | `SmartDashboard.put*` / Shuffleboard scattered through subsystems |
| 2 | Structured lightweight logging | DogLog, Epilogue (`@Logged`), URCL, or systematic NetworkTables publishing; AdvantageScope layouts committed |
| 3 | AdvantageKit | `@AutoLog` inputs structs, `Logger.processInputs` throughout; full-match logging to file |
| 4 | Replay + operational diagnostics | Log replay actually exercised (replay IO variants, replay vendordep configs) and/or self-check fault reporting (3061/3015-style `FaultReporter`, system-check commands) |

**Grep:** `doglog`, `Epilogue`, `@Logged`, `URCL`, `org.littletonrobotics.junction`, `Logger.processInputs`, `@AutoLog`, `FaultReporter`, `SystemCheck`, committed `.json` AdvantageScope layouts.

**Caution:** AdvantageKit vendored but with `processInputs` on one subsystem out of ten is level 2, not 3. The level is about coverage, not presence — gauge coverage by the *count* of `Logger.processInputs` / `recordOutput` call sites relative to the subsystem roster (a handful = partial; dozens across every subsystem = real L3).

---

## D6 — Autonomous & path planning

*Are the three path concerns (authored path, optimal trajectory, reactive avoidance) present and pulled apart?*

| Level | Anchor | Observable indicators |
|---|---|---|
| 0 | Timed / dead-reckoned auto | Drive-by-stopwatch autos; no trajectory following |
| 1 | Basic closed-loop auto | Encoder/gyro-based moves; maybe WPILib trajectory following on a simple path |
| 2 | PathPlanner autos | `.path`/`.auto` files, PathPlannerLib configured with real constraints; multiple competition autos |
| 3 | Optimized trajectories | Choreo (`.traj`/`.chor` files actually referenced in code) where time matters, typically alongside PathPlanner; on-the-fly driving to poses (align-to-target commands) |
| 4 | Reactive planning | Repulsor/potential-field or equivalent dynamic obstacle avoidance; superstructure states exposed as auto actions; auto selection infrastructure |

**Grep:** `pathplanner` dir under `src/main/deploy`, `PathPlannerLib.json`, `choreo` / `.traj` / `.chor`, `Repulsor`, `RepulsorField`, `AutoBuilder`, `AutoBuilder.pathfind*` (on-the-fly, L3).

**Confirm use — this is the lowest-trust dimension (κ 0.60).** Choreo `.traj`/`.chor` *files* count for nothing on their own: in the corpus, 15 of the teams with Choreo files **never reference them in code**, and PathPlanner `.auto` files frequently carry `choreoAuto:false`. Require an actual code reference — `fromChoreoTrajectory(...)`, `Choreo.loadTrajectory(...)`, a `choreo.auto.AutoFactory` — before crediting Choreo at L3. Likewise confirm `AutoBuilder.configure(...)` is wired with real constraints, not just imported.

---

## D7 — Localization & vision

*What does the robot believe about where it is, and how is that belief maintained?*

| Level | Anchor | Observable indicators |
|---|---|---|
| 0 | None | No vision, odometry unused in decisions |
| 1 | Targeting only | Limelight tx/ty servoing on a target; no pose estimation |
| 2 | Pose estimation | AprilTag pose via PhotonVision/Limelight MegaTag feeding `SwerveDrivePoseEstimator.addVisionMeasurement` |
| 3 | Fused, filtered estimation | Vision std-dev tuning, multi-camera fusion, rejection logic; vision behind an IO interface with sim variant |
| 4 | World model as architecture | A dedicated `RobotState` class owning pose + game-piece state with time-interpolated buffers; localization decoupled from control |

**Grep:** `photonlib`, `PhotonCamera`, `LimelightHelpers`, `addVisionMeasurement`, `SwerveDrivePoseEstimator`, `RobotState`, `TimeInterpolatableBuffer`, `MegaTag`. For the **L3 fused-and-filtered** rung, the discriminating markers are `setVisionMeasurementStdDevs` (dynamic std-dev tuning) and a `VisionIO` interface with a sim variant (vision decoupled from `Drive`); for **L4**, a dedicated `RobotState` whose pose lives in a `TimeInterpolatableBuffer`/`ConcurrentTimeInterpolatableBuffer`.

**Confirm use (κ 0.60).** `addVisionMeasurement` is near-universal (50/55 teams) — it is the L2 floor, not evidence of L3. The level is set by the *filtering* (rejection logic, per-tag std-devs) and *architecture* (IO seam, central world-model), which you must read to see.

---

## D8 — Sustainability & process (artifact-based)

*Will this codebase survive its seniors graduating? Scored from artifacts only — treat as a floor.*

| Level | Anchor | Observable indicators |
|---|---|---|
| 0 | Bare code drop | No README beyond GradleRIO default; no docs, no structure conventions |
| 1 | Basic hygiene | Real README (build/deploy instructions); consistent package structure; constants organized |
| 2 | Onboarding & standards | Contributing/style docs; formatter or linter configured (spotless/checkstyle in `build.gradle`); training or template repos exist in the team's org |
| 3 | CI + team library | GitHub Actions on the season repo; a maintained season-independent library or `lib/` package carried across seasons (`SuperCORE`, `WarlordsLib`, `3128-common`, `NOMADBase` pattern) |
| 4 | Program-grade infrastructure | Library is versioned/consumed as a dependency (not copy-paste); multi-robot variant structure; docs generated or maintained; evidence of release discipline |

**Grep:** `README.md` length and content, `CONTRIBUTING`, `spotless`, `checkstyle`, `.github/workflows`, separate `lib`/`common` repos in team folder, `shared/` or variant packages.

---

## Scoresheet template

One row per team. The sum is reported, but the profile is the finding.

| Team | Repo scored | D1 Arch | D2 Coord | D3 Sim | D4 Test | D5 Log | D6 Auto | D7 Vision | D8 Sustain | Σ /32 | Profile notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | | |

---

## Reading the profile: common shapes

- **Balanced climber** — all dimensions within ±1 of each other. The ladder is working; next step is whatever's lowest.
- **Architecture without verification** (D1 ≥ 3, D3/D4 ≤ 1) — adopted the IO layer's *form* without its *payoff*. Likely copied a template (check against 5712-style AdvantageKit templates). Highest-leverage intervention: one unit test.
- **Tooling adopter** (D5/D6 high, D1/D2 low) — uses AdvantageScope/PathPlanner/Choreo but the code underneath is baseline command-based. Tools were installable; architecture wasn't. Intervention: an IO layer on one subsystem.
- **Template inheritor** — D1 = 3 exactly matching a known public template, everything else low. Distinguish from organic adoption by checking whether IO interfaces exist for *their* mechanisms or only the swerve they forked.
- **Legacy program** — competent older patterns (solid command-based, good autos) with no post-2022 tooling. Different conversation: modernization, not fundamentals.
- **Verification ceiling** (everything ≥ 3 except D4) — the regional-elite profile; even strong teams rarely test. D4 ≥ 2 is the rarest marker in the national corpus and the clearest signal of real software-engineering culture.

---

## Suggested scoring procedure

1. Identify the latest real season repo; record season and language.
2. Run the grep cheat-sheet (one pass per dimension) to generate candidate levels.
3. Open the files behind every positive hit — confirm use, not presence. Adjust the level.
4. Check the team's other repos *only* for D8 (libraries, templates, training).
5. Write 2–3 sentences of profile notes: the shape, the likely explanation, the one highest-leverage next step for the team.

