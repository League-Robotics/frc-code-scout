---
title: The Elite & League Architectures
weight: 1
---

# Inside Competition Robot Code — The Elite and League Architectures

**A three-part wiki.** Part I documents the **Elite Architecture**: the architecture that top FRC
teams have actually converged on, reconstructed empirically from reading dozens of public codebases
and validated against competition results. Part II is the **anatomy** — a component-by-component
reference that opens the hood on each major piece. Part III presents the **League Architecture**: our
own evolved proposal, the same ideas pushed to a single unifying abstraction and made
language-portable.

> **Status: planning outline.** This page is the annotated table of contents — the hierarchy, a
> description of each chapter, and the source documents in `knowledge/` (and `docs/review/`) each
> chapter is written from. This wiki is **self-contained and supersedes** the generated `docs/book`;
> chapters absorb the cited source material rather than linking out to it.

---

## How to read it

The wiki is hyperlinked like a wiki, but it has a spine you can read straight through like a book.
**Part I builds the case and explains what the architecture is** — at a glance, not in great detail.
**Part II is the engineering reference** — how each component is actually built. **Part III makes the
argument** that all of it is special cases of one shape, and that naming the shape buys logging,
replay, testing, and ROS portability at every scale.

The dividing line between Parts I and II is **depth, not topic**. Part I answers *what is it, is it
true, and does it matter*; Part II answers *how does it work and what do I build*. A reader who
finishes Part I knows what the three seams are and how a goal becomes a motor voltage — in a
sentence or two each. Part II is where the hood comes off.

- **New to the project?** Read Part I straight through (ch. 1 → 14).
- **Building a robot?** Read the at-a-glance overview (ch. 4) and the rubric (ch. 3), then work
  through Part II for the mechanics, then Part III.
- **Need the detail on one component?** Jump straight to its Part II chapter (ch. 15 → 23).
- **Evaluating the proposal?** Part III (ch. 24 → 32), ending on the open questions in ch. 32.

The numbering is the book order. The lettered sections are the shelf it sits on.

---

# Part I — The Elite Architecture *(descriptive: what top teams actually do)*

*The architecture nobody designed and everybody arrived at. Reconstructed from the corpus, turned
into a measurement instrument, and checked against who actually wins.*

## A. Method and instrument

### 1. How we read the corpus
How the study was conducted end to end: which teams, how repos were selected and cloned, the
tree-sitter → DuckDB index that lets us count markers across 55 season repos, and the cardinal rule
that makes the findings trustworthy — **score what's *used*, not what's *present*** (confirm every
claim by opening the cited file). Establishes the evidentiary standard for the whole of Part I.
*Sources: `examples/methodology.md`, `corpus-analysis/02-frc-37-team-survey.md` (corpus framing),
`knowledge/INDEX.md`, the prevalence table in `rubric/rubric.md`, `AGENTS.md`.*

### 2. The baseline everyone starts from
The WPILib command-based framework — subsystems (things the robot *has*) and commands (things the
robot *does*), wired in `RobotContainer`. This is real but shallow modularity: a command still calls
subsystem methods, a subsystem still holds motor objects. Everything interesting in the architecture
is the layers elite teams insert *above and below* that line, so this chapter is the reference point
the rest measures against.
*Sources: `corpus-analysis/02-frc-37-team-survey.md` (baseline + "modularity is a ladder").*

### 3. Eight dimensions of sophistication — the rubric
The measuring instrument: D1 Architecture, D2 Coordination, D3 Simulation, D4 Testing, D5 Logging,
D6 Autonomous/Path, D7 Vision/Localization, D8 Sustainability — each scored 0–4 against anchored,
observable indicators. Explains *why dimensions rather than one ladder score* (teams adopt unevenly;
the profile shape is the signal) and ships the measured corpus prevalence so a reader can calibrate a
marker as "table stakes" vs "ceiling signal."
*Sources: `rubric/rubric.md`.*

## B. The architecture and its seams

### 4. The architecture at a glance
The orienting overview: the whole Elite Architecture in one chapter, at low resolution. The three
structural **seams** (IO, state, coordination) and the one cross-cutting decision (the logging
contract); how a goal flows down to motors and how state flows back up; and the organizing principle
— **build the seams, defer the payoffs**, so every advanced capability is an addition at a known
attachment point rather than a rewrite. A reader who stops here still understands the architecture.
The mechanics of each piece are Part II.
*Sources: `build-spec/elite-architecture.md` (§1–§2 thesis + layered overview).*

### 5. The IO seam — the spine
The most important pattern in the corpus, stated and motivated: one `XxxIO` interface per subsystem
at the line between subsystem logic and physical devices, with interchangeable real/sim/replay
implementations — the **Strategy pattern at subsystem granularity**. What it is, how common it is
(24/55), and why it is the precondition for sim, tests, and replay. Rubric D1. *(Mechanics — the
loop-above/below decision, the inputs struct, naming — are Part II ch. 16–17.)*
*Sources: `corpus-analysis/03-io-layer-strategy-pattern.md`,
`build-spec/subsystems/00-anatomy-of-a-subsystem.md`.*

### 6. The state seam — `RobotState` and the world model
A single object owning the robot's best estimate of the world behind a pose estimator: sensors
write, decisions read. The corpus split that matters — pose estimation is near-universal
(`addVisionMeasurement` in 50/55), but a *centralized* world model (26/55) is the elite move. Rubric
D7. *(The estimator internals and fusion mechanics are Part II ch. 20.)*
*Sources: `build-spec/subsystems/07-robotstate.md`, prevalence table in `rubric/rubric.md`.*

### 7. The coordination seam — the superstructure
Where teams actually diverge. One robot-wide *goal* fanned out to per-subsystem setpoints through a
single guarded transition function — intent separated from execution, with interlocks in one place.
Names the six coordination paradigms the corpus exhibits without yet dissecting them. Rubric D2.
*(The paradigms in depth — FSMs, state graphs, behavior trees — are Part II ch. 22–23.)*
*Sources: `build-spec/subsystems/08-superstructure.md`,
`corpus-analysis/02-frc-37-team-survey.md` (coordination paradigms).*

### 8. The drivetrain — the architecturally special subsystem
Why the drivetrain gets its own chapter even in the overview: it is the only near-universal subsystem
(94%) and the only thing that is both actuator and primary sensor — its `Pose` is the most-consumed
value on the robot. The architecture spectrum from CTRE-generated (~63%) to teams that own a real
seam (~27%). *(The swerve internals — modules, kinematics, odometry — are Part II ch. 19.)*
*Sources: `corpus-analysis/08-drivetrain-as-architecture.md`.*

## C. The practices around the seams

### 9. Cross-cutting practices — simulation, testing, logging
The three disciplines that hang off the IO seam and separate engineering culture from cargo cult.
Simulation (run modes, HAL sim, maple-sim, AdvantageScope — D3); testing (IO-sim-as-mock, the
sim-time harness, CI — D4); logging (the inputs-struct contract; the println → DogLog/Epilogue →
AdvantageKit-with-replay ladder — D5). The corpus truth: almost everyone builds the seam, almost no
one collects the test/replay dividend.
*Sources: `build-spec/simulation.md`, `build-spec/testing.md`, `build-spec/logging.md`.*

## D. Growth and proof

### 10. The novice-to-elite maturity ladder
How a program actually climbs over four to five seasons — paired engineering and team-process leaps,
sequenced by **pain, not prestige**, and the iron rule "you rewrite in the offseason, never during
build season." The five phases, the motivating pain at each rung, and the three habits (simulate,
review, retain) that carry a team across the graduation cliff.
*Sources: `corpus-analysis/04-novice-to-elite-progression.md`.*

### 11. What the architecture actually predicts
The validation: 24 San Diego teams scored and correlated with Statbotics EPA. Code sophistication
tracks results only moderately (ρ ≈ 0.55) — and the per-dimension breakdown is the real finding
(D8, D6, D7 track results; D3, D4 barely do). The outliers carry the signal (sophisticated-but-
losing 3647; modest-but-winning 4419). The honest caveats: correlation not causation, program-age
confound, small n.
*Sources: `survey/sd-frc-final-report.md`, `survey/sd-frc-correlations.csv`,
`survey/sd-frc-scores-pilot.md`, `examples/patribots-four-year-scoring.md`,
`examples/sample-score-output-reefscape2025.md`.*

## E. Synthesis and frontier

### 12. Foundation-first — how the architecture grows without rewrites
The build philosophy that ties Part I together: the add-on progression (each rung an addition at a
named seam), the deferred-dividend rungs teams skip and shouldn't (sim → tests → replay), the
tool-per-seam map, and the one rule that carries it all — **no vendor type above the IO line.** Where
ch. 4 says *what it is*, this says *in what order you build it and why that order is safe.*
*Sources: `build-spec/elite-architecture.md` (§3–§7), `build-spec/code-review-principles.md`.*

### 13. Lessons from outside FRC
The outside-in view: what ROS / Nav2 / MoveIt / autonomous-driving treat as table stakes that FRC
skips — graceful degradation, lifecycle, process discipline — and the spec-in/code-out generators
(RobotBuilder, Tuner X, YAGSL, LLMs) scored against the IO seam (all optimize time-to-drive, not
swappability). Sets up Part III by naming what the Elite Architecture is still missing.
*Sources: `corpus-analysis/06-lessons-from-broader-robotics.md`,
`corpus-analysis/07-code-generators.md`.*

### 14. Alternatives — legitimate deviations
Sound, uncommon, situational patterns that aren't the default but earn a place: capability-typed
devices (named by capability, not vendor), physical-plant simulation (truth as the dual of estimate),
state-graph coordination, and behavior trees — each with its guardrails and an honest statement of
when it's right and when it's over-engineering. The bridge from "what teams do" to "what we'd do
differently."
*Sources: `alternatives/README.md`, `alternatives/01-capability-typed-devices.md`,
`alternatives/02-physical-plant-simulation.md`, `alternatives/03-state-graph-coordination.md`,
`alternatives/04-behavior-trees.md`.*

---

# Part II — Anatomy of the Elite Architecture *(reference: how each component is built)*

*The hood comes off. Each chapter takes one major component of Part I and shows the engineering — the
contracts, the decisions, the real variants in the corpus, and what to build.*

## F. The control path and abstraction

### 15. The control path, end to end
The orienting map for the whole reference: how a teleop binding or an autonomous routine becomes a
superstructure goal, becomes a subsystem setpoint, becomes an IO call, becomes a motor voltage — and
how measured state flows back up the same path. The 20 ms loop in order (read → log → decide →
actuate), run-mode selection (REAL / SIM / REPLAY), and the single point that chooses
implementations. Every later chapter is a drill-down into one station on this path.
*Sources: `build-spec/elite-architecture.md` (§2.3 runtime loop, §5 scenarios).*

### 16. Hardware abstraction and the IO line
What "hardware abstraction" means precisely versus "the IO layer as a *location*" — they are not the
same thing, and conflating them is a common error. Ports-and-adapters at subsystem granularity; the
two deliberate decisions (where the control loop sits — loop-above vs loop-below the line; inputs
struct vs plain getters); and the vendor-confinement rule, including how it actually leaks (22 of 24
IO teams import a vendor type above the line).
*Sources: `corpus-analysis/03-io-layer-strategy-pattern.md`,
`build-spec/subsystems/00-anatomy-of-a-subsystem.md`, `build-spec/code-review-principles.md`.*

### 17. Motor interfaces
The device-level contract in depth: how teams actually talk to motors. The six reusable `MotorIO`
contracts found across the corpus and the design axes that distinguish them; loop placement and
on-motor vs on-RIO control; and the capability-typed alternative (named by capability, not vendor)
with a hardware object below the line.
*Sources: `corpus-analysis/05-motor-io-interfaces.md`, `alternatives/01-capability-typed-devices.md`.*

## G. The subsystems

### 18. Subsystem archetypes
The IO quartet (`XxxIO` / `Inputs` / hardware impl / `IOSim`) applied per control archetype, with the
WPILib sim model each uses: linear position (elevator, climber — `ElevatorSim`), rotational position
(arm, pivot, wrist, turret — `SingleJointedArmSim`), velocity (shooter, flywheel — `FlywheelSim`),
and roller / game-piece (intake, indexer — `DCMotorSim` + the game-piece sensor). The shared template
and the mock/library/vendor ethic every subsystem applies.
*Sources: `build-spec/subsystems/00-anatomy-of-a-subsystem.md` through `04-roller-gamepiece.md`.*

### 19. The drivetrain subsystem
The swerve special case in engineering depth: the multi-interface seam (`ModuleIO` ×4 + `GyroIO`),
kinematics and odometry, the optional `SwerveSetpointGenerator`, and the empirical architecture
spectrum (CTRE-generated vs owned seam) with the 254/2910 elite package layout and the
`CommandSwerveDrivetrain` / `SwerveRequest` / `SwerveDriveState` usage rankings.
*Sources: `build-spec/subsystems/06-swerve-drivetrain.md`,
`corpus-analysis/08-drivetrain-as-architecture.md`.*

## H. Perception and coordination

### 20. The world model
`RobotState` and sensor fusion in depth: the pose estimator, the time-interpolated history buffer,
how odometry and vision corrections fuse, and why centralizing the estimate (rather than letting the
drive subsystem privately own it) is what lets vision, pathfinding, and autos share one consistent
world model. The state seam's internals.
*Sources: `build-spec/subsystems/07-robotstate.md`.*

### 21. Vision systems
The dedicated vision chapter. The pipeline end to end — coprocessor (PhotonVision / Limelight) →
observation (pose + tags + latency) → `VisionIO` → `RobotState.addVisionMeasurement` — and the
`VisionIO` swap that makes the camera vendor interchangeable. What teams actually run and how far it
goes: AprilTag pose estimation (the near-universal floor), neural game-piece detection (the rung
past), and emerging VIO / QuestNav. What the system *produces* — pose estimate, target bearing,
standard deviations, latency — and exactly who consumes each output (the fusion, the aim, the auto).
Std-dev / ambiguity gating: how a measurement is trusted or rejected.
*Sources: `build-spec/subsystems/05-vision-sensor.md`, prevalence table in `rubric/rubric.md`,
`build-spec/other-topics.md` (neural detection, QuestNav), `corpus-analysis/06-lessons-from-broader-robotics.md`.*

### 22. Coordination I — state machines and the superstructure
The coordination seam in depth: the wanted/current FSM, the centralized `RobotManager`, guarded
transitions, and where interlocks live (the one object that sees all mechanisms at once). The
foundation `switch`-over-goal-enum form and how a real interlock is sequenced safely. The most common
real coordinators in the corpus.
*Sources: `build-spec/subsystems/08-superstructure.md`,
`corpus-analysis/02-frc-37-team-survey.md` (coordination paradigms).*

### 23. Coordination II — state graphs and behavior trees
The far end of the coordination ladder: coordination as **graph search** over a superstructure state
graph (254/6328's jgrapht; A\* over a discretized configuration space), and **behavior trees** — the
re-ticked SUCCESS/FAILURE/RUNNING tree borrowed from game AI (3015's full runtime + visual editor).
When each beats an FSM, and why explicit behavior trees are nearly absent in FRC while their
command-group cousin is universal.
*Sources: `alternatives/03-state-graph-coordination.md`, `alternatives/04-behavior-trees.md`,
`corpus-analysis/02-frc-37-team-survey.md`.*

---

# Part III — The League Architecture *(prescriptive: what we propose)*

*The Elite Architecture, evolved. Parts I and II's components turn out to be instances of one shape;
naming that shape is the whole proposal.*

## I. The unifying idea

### 24. From Elite to League — what we keep, what we change
The bridge chapter. We keep every Elite commitment (the IO seam, intent/execution split, vendor
confinement, the deferred-dividend discipline) and change one thing: instead of three differently
shaped seams plus a pile of subsystems, we observe they are all the **same recursive component** and
build to that contract deliberately. States the thesis, the scope, and what "portable" buys.
*Sources: `specs/portable-component-model.md` (§0–§1), `build-spec/elite-architecture.md`,
`corpus-analysis/06-lessons-from-broader-robotics.md`.*

### 25. The Portable Component Model — the `Block`
The core of the proposal. Every active thing — motor, sensor, subsystem, `RobotState`,
superstructure — is a **configured transfer function with memory**: `Config` once, then
`(State′, Command_out[]) = update(Command_in, Observations)` each tick. Four serializable PODs and
one pure step. The non-obvious payoff: **which channels a block fills *is* its type** (the
fill-pattern taxonomy). Emission is a return value, not a side effect; it's a discipline, not a base
class; it's the in-process ROS 2 node. Recommends the name `Block`.
*Sources: `specs/portable-component-model.md` (the whole spec).*

## J. The instances

### 26. The portable motor interface — the leaf block
The Block contract specialized to a leaf actuator: two serializable PODs (`Command`/`MotorState`,
named `u`/`x`), nullable payloads, `oneof` control modes, capability tiers, REP-103 units, and a
proto3 source-of-truth with a generated ROS bridge. Contrasted with the corpus survey of how other
teams talk to motors (ch. 17) so the design choices are visible as choices.
*Sources: `specs/portable-motor-interface.md`, `corpus-analysis/05-motor-io-interfaces.md`.*

### 27. The portable swerve interface — the mid-level block
A drive subsystem as a block whose children are four module blocks, each two motor blocks. The
five-layer model (WPILib math → `ModuleIO`/`GyroIO` seam → module logic → drive + setpoint generator
→ `SwerveRequest` vocabulary): "AdvantageKit's seam + CTRE's vocabulary on WPILib's math." Shows
seam-granularity as literally *where you draw a block boundary*.
*Sources: `specs/portable-swerve-interface.md`, `corpus-analysis/08-drivetrain-as-architecture.md`.*

### 28. `RobotState` and `Superstructure` as blocks
The two higher seams recovered as instances: `RobotState` is "a sensor that fuses" (an observer);
the superstructure is a block whose `Command_out` feeds subsystems instead of motors. Why a subsystem
and an executive are the *same kind*, why `State` splits into estimate + status above the leaf, and
why every level is named `…State`.
*Sources: `specs/portable-component-model.md` (§3, §5, §10),
`build-spec/subsystems/07-robotstate.md`, `build-spec/subsystems/08-superstructure.md`.*

## K. The dividends and portability

### 29. Telemetry, replay, and tests — for free, at every scale
What four loggable PODs per block buy: snapshot every block's channels each tick and you have
AdvantageKit-grade replay and telemetry for the *entire robot at every altitude*, not just motors; a
pure `update` makes every block unit-testable by replaying recorded inputs. The Elite inputs-struct
idea (ch. 16) generalized from leaves to executives.
*Sources: `specs/portable-component-model.md` (§2, §4), `build-spec/logging.md`,
`build-spec/testing.md`, `build-spec/simulation.md`.*

### 30. Lifecycle and graceful degradation
Baking in the discipline FRC most conspicuously skips (ch. 13). A real component has a ROS-style
managed lifecycle; health is a field in `State.status`, not an exception; and the `*IONull`
null-object *is* the block in its `fault` state. Degradation becomes a lifecycle transition of the
standard shape rather than a special case bolted on.
*Sources: `specs/portable-component-model.md` (§7),
`corpus-analysis/06-lessons-from-broader-robotics.md` (§5), `alternatives/02-physical-plant-simulation.md`.*

### 31. The ROS bridge and language portability
The proof the factoring is right: a block maps to a ROS 2 node with no impedance mismatch
(Config↔parameters, Command_in↔topic/goal, State↔topic + feedback, Command_out↔published topics,
`update`↔spin). "Keep the message semantics, drop the message transport" — in-process typed calls on
the RIO; a real message only on the one inter-process edge (RIO ↔ coprocessor). The proto3
source-of-truth that makes it language-neutral.
*Sources: `specs/portable-component-model.md` (§8, §11),
`specs/portable-motor-interface.md` (proto3 / ROS bridge).*

## L. Maturity of the proposal

### 32. Open questions and the road to a build recipe
The honest close: the League model is a living proposal, not finished doctrine. The two load-bearing
open questions (is `Observations` a fifth channel or just "children's `State`"? generic scheduler vs
hand-wired composition?) and the structural gaps the review surfaced — execution order (two-pass),
`RobotState`'s cross-cutting dual-graph (commands form a tree, state a DAG), the WPILib integration
choice (wrap blocks in `Subsystem.periodic()`), and splitting `Config` retuning from mode switches.
What must close before `scaffold-robot`/`add-subsystem` emit to this contract by default.
*Sources: `docs/review/portable-component-model-review.md`,
`specs/portable-component-model.md` (Open Questions).*

---

# Appendices *(reference, not narrative)*

- **Appendix A — The rubric in full.** The complete D1–D8 anchors and grep cheat-sheet, for scoring.
  *Source: `rubric/rubric.md`.*
- **Appendix B — The San Diego scoresheet.** Full per-team D1–D8 vectors, EPA, and the per-dimension
  correlation table. *Sources: `survey/sd-frc-final-report.md`, `survey/*.csv`,
  `survey/sd-frc-inventory.md`, `survey/sd-ftc-inventory.md`.*
- **Appendix C — Worked example: the Patribots, four years.** A full single-team, multi-season
  analysis to imitate. *Sources: `examples/patribots-four-year-scoring.md` (+ `.pdf`).*
- **Appendix D — Glossary and naming decisions.** Block, seam, IO line, `u`/`x`, estimate vs status,
  and why `Block` over `Component`/`Node`/`Unit`/`Module`. *Sources:
  `specs/portable-component-model.md` (§12), `corpus-analysis/03-io-layer-strategy-pattern.md`.*
- **Appendix E — Other advanced topics.** Additive techniques that aren't architectural alternatives:
  state-space/LQR, swerve setpoint generator, threaded odometry, self-check, replay-as-test, QuestNav.
  *Source: `build-spec/other-topics.md`.*
- **Appendix F — Source-document crosswalk.** A table mapping every `knowledge/` file to the
  chapter(s) that absorb it, so nothing in the corpus is orphaned by the rewrite.

---

## Open decisions for the next pass

1. **Part I ↔ Part II overlap is real and intended — keep it honest.** Several components appear in
   both (IO seam: ch. 5 + 16–17; world model: ch. 6 + 20; coordination: ch. 7 + 22–23; drivetrain:
   ch. 8 + 19). The rule is depth: Part I states and motivates, Part II builds. When drafting, each
   Part I seam chapter should end with an explicit "deep dive: Part II ch. X" pointer, and Part II
   should not re-argue *why* — only *how*. Decide if the two overview chapters (ch. 4 at-a-glance,
   ch. 12 foundation-first) stay distinct or merge.
2. **Chapter granularity in Part II's instances and Part III.** The motor and swerve specs are long
   (752 and 530 lines); ch. 26–27 and possibly ch. 17/19 may each split into 2–3 wiki pages. The
   subsystem-archetype chapter (ch. 18) folds five source docs — it may want to be five short pages
   under one section rather than one long chapter. Decide when drafting.
3. **Coordination as one chapter or two.** Ch. 22 (state machines) and ch. 23 (state graphs +
   behavior trees) are split because both are meaty and you named them separately; they could merge
   into one "Coordination paradigms" chapter with subsections.
4. **Tooling scope.** Whether the wiki documents the scoring/scaffolding *tooling* (`analyze-team`,
   `scaffold-robot`, the plugin skills in `AGENTS.md`) or stays purely architectural. Currently out
   of scope.
