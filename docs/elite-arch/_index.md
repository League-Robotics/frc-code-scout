---
title: The Elite & League Architectures
weight: 1
---

# Inside Competition Robot Code — The Elite and League Architectures

**A four-part wiki.** Part I documents the **Elite Architecture**: the architecture that top FRC
teams have actually converged on, reconstructed empirically from reading dozens of public codebases
and checked against competition results (the correlation is moderate and heavily confounded by
program maturity — see ch. 34). Part II is the **anatomy** — a component-by-component
reference that opens the hood on each major piece. Part III presents the **League Architecture**: our
own evolved proposal, the same ideas pushed to a single unifying abstraction and made
language-portable. Part IV is the **measurement instrument** — the rubric, its calibration, and a
four-year case study.

> **This page is the annotated table of contents** — the hierarchy, a description of each chapter, and
> the source documents in `knowledge/` (and `docs/review/`) each chapter is written from. Some cited
> sources have since moved under `knowledge/archived/`; the crosswalk records each file's disposition. This wiki is
> **self-contained and supersedes** the generated `docs/book`; chapters absorb the cited source material
> rather than linking out to it. The full source-to-chapter map is
> [Appendix C — the crosswalk](appendices/source-crosswalk.md).

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

- **New to the project?** Read Part I straight through (ch. 1 → 9).
- **Building a robot?** Read the five-views overview (ch. 2), then the rubric and maturity ladder in
  the [How We Developed This](appendices/how-we-developed-this/) appendix, then work through Part II for
  the mechanics, then Part III.
- **Need the detail on one component?** Jump straight to its Part II chapter (ch. 15 → 23).
- **Evaluating the proposal?** Part III (ch. 24 → 32), ending on the open questions in ch. 32.
- **Scoring a team?** Read the rubric in full (ch. 33), then the caveats in the San Diego scoresheet
  (ch. 34), and use the Patribots study (ch. 35) as the worked example.

The numbering is the book order. The lettered sections are the shelf it sits on. One note on the
numbers: chapters 10–14 (and section letter E) don't exist — that material became
[Appendix A](appendices/how-we-developed-this/), and the numbering is preserved so older citations
still resolve. Nothing is missing.

---

# Part I — The Elite Architecture *(descriptive: what top teams actually do)*

*The architecture nobody designed and everybody arrived at. Reconstructed from the corpus, turned
into a measurement instrument, and checked against competition results.*

## A. Orientation

### 1. The baseline and the shape
The shared starting point and the two lenses the rest of Part I reads the architecture through. WPILib
command-based — subsystems (things the robot *has*) and commands (things it *does*), wired in
`RobotContainer` — and the two joints of coupling it leaves (command → concrete subsystem, subsystem →
concrete devices) that every elite addition targets. Then the framing for the whole part: **positive
space** (the views — where the parts are) and **negative space** (the seams — the joints between them),
carrying the organizing rule **build the seams, defer the payoffs.**
*Sources: `corpus-analysis/02-frc-37-team-survey.md` (baseline + "modularity is a ladder"),
`build-spec/elite-architecture.md` (§1).*

### 2. The architecture in five views
The orienting overview, built on Kruchten's **4+1 view model**. The *logical* view (the six recurring
components and how command flows down while state flows up), the *development* view (the library
layering — WPILib floor, vendor libraries, and the rule that confines them below the IO line), the
*process* view (the 20 ms read → log → decide → actuate loop and the path of a driver packet), the
*physical* view (the robot schematic — roboRIO, the CAN and CANivore buses, coprocessors on Ethernet),
and two *scenarios* that put the views in motion. A reader who stops here understands the architecture;
the seams and Part II add resolution.
*Sources: `build-spec/elite-architecture.md` (§1–§2 thesis + layered overview + runtime loop).*

## B. The seams *(the negative space — the joints between the parts)*

### 3. The IO seam — the spine
The most important pattern in the corpus, stated and motivated: one `XxxIO` interface per subsystem
at the line between subsystem logic and physical devices, with interchangeable real/sim/replay
implementations — the **Strategy pattern at subsystem granularity**. What it is, how common it is
(24/55), and why it is the precondition for sim, tests, and replay. Rubric D1. *(Mechanics — the
loop-above/below decision, the inputs struct, naming — are Part II ch. 16–17.)*
*Sources: `corpus-analysis/03-io-layer-strategy-pattern.md`,
`build-spec/subsystems/00-anatomy-of-a-subsystem.md`.*

### 4. The state seam — `RobotState` and the world model
A single object owning the robot's best estimate of the world behind a pose estimator: sensors
write, decisions read. The corpus split that matters — pose estimation is near-universal
(`addVisionMeasurement` in 50/55), but a *centralized* world model (26/55) is the elite move. Rubric
D7. *(The estimator internals and fusion mechanics are Part II ch. 20.)*
*Sources: `build-spec/subsystems/07-robotstate.md`, prevalence table in `rubric/rubric.md`.*

### 5. The coordination seam — the superstructure
Where teams actually diverge. One robot-wide *goal* fanned out to per-subsystem setpoints through a
single guarded transition function — intent separated from execution, with interlocks in one place.
Names the six coordination paradigms the corpus exhibits without yet dissecting them. Rubric D2.
*(The paradigms in depth — FSMs, state graphs, behavior trees — are Part II ch. 22–23.)*
*Sources: `build-spec/subsystems/08-superstructure.md`,
`corpus-analysis/02-frc-37-team-survey.md` (coordination paradigms).*

### 6. The drivetrain — the architecturally special subsystem
Why the drivetrain gets its own chapter even in the overview: it is the only near-universal subsystem
(94%) and the only thing that is both actuator and primary sensor — its `Pose` is the most-consumed
value on the robot. The architecture spectrum from CTRE-generated (~63%) to teams that own a real
seam (~27%). *(The swerve internals — modules, kinematics, odometry — are Part II ch. 19.)*
*Sources: `corpus-analysis/08-drivetrain-as-architecture.md`.*

## C. The practices around the seams

### 7. Cross-cutting practices — simulation, testing, logging
The three disciplines that hang off the IO seam and separate engineering culture from cargo cult.
Simulation (run modes, HAL sim, maple-sim, AdvantageScope — D3); testing (IO-sim-as-mock, the
sim-time harness, CI — D4); logging (the inputs-struct contract; the println → DogLog/Epilogue →
AdvantageKit-with-replay ladder — D5). The corpus truth: almost everyone builds the seam, almost no
one collects the test/replay dividend.
*Sources: `build-spec/simulation.md`, `build-spec/testing.md`, `build-spec/logging.md`.*

## D. The frontier

### 8. Alternatives — legitimate deviations
Sound, uncommon, situational patterns that aren't the default but earn a place: capability-typed
devices (named by capability, not vendor), physical-plant simulation (truth as the dual of estimate),
state-graph coordination, and behavior trees — each with its guardrails and an honest statement of
when it's right and when it's over-engineering. The bridge from "what teams do" to "what we'd do
differently."
*Sources: `alternatives/README.md`, `alternatives/01-capability-typed-devices.md`,
`alternatives/02-physical-plant-simulation.md`, `alternatives/03-state-graph-coordination.md`,
`alternatives/04-behavior-trees.md`.*

### 9. Other advanced topics
Additive techniques that specialize a seam rather than replace it — the category next to the
alternatives: state-space/LQR, the swerve setpoint generator, high-frequency threaded odometry,
self-check diagnostics, replay-as-regression-test, neural game-piece detection, reactive autonomy, and
QuestNav. Each attaches at an existing seam, keeps its vendor dependency below the IO line, and can be
added or removed without disturbing the rest of the robot.
*Source: `build-spec/other-topics.md`.*

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
graph (explicit state graphs in ~5 teams; genuine A\* over a discretized configuration space in 254
alone), and **behavior trees** — the
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

### 25. The Portable Component Model — the faceplate
The core of the proposal. Every active thing — motor, sensor, subsystem, `RobotState`,
superstructure — is a **configured transfer function with memory**: `Config` once, then
`(State′, Command_out[]) = update(Command_in, Observations)` each tick. Every component presents the
same **faceplate** — four serializable PODs and one pure step. The non-obvious payoff: **which
channels a component fills *is* its type** (the fill-pattern taxonomy). Emission is a return value,
not a side effect; it's a discipline, not a base class; it's the in-process ROS 2 node. Names the
shape *faceplate* — a prose term, never a type.
*Sources: `specs/portable-component-model.md` (the whole spec).*

## J. The instances

### 26. The portable motor interface — the leaf component
The faceplate contract specialized to a leaf actuator: two serializable PODs (`Command`/`MotorState`,
named `u`/`x`), nullable payloads, `oneof` control modes, capability tiers, REP-103 units, and a
proto3 source-of-truth with a generated ROS bridge. Contrasted with the corpus survey of how other
teams talk to motors (ch. 17) so the design choices are visible as choices.
*Sources: `specs/portable-motor-interface.md`, `corpus-analysis/05-motor-io-interfaces.md`.*

### 27. The portable swerve interface — the mid-level component
A drive subsystem as a component whose children are four module components, each two motors. The
five-layer model (WPILib math → `ModuleIO`/`GyroIO` seam → module logic → drive + setpoint generator
→ `SwerveRequest` vocabulary): "AdvantageKit's seam + CTRE's vocabulary on WPILib's math." Shows
seam-granularity as literally *where you draw a component boundary*.
*Sources: `specs/portable-swerve-interface.md`, `corpus-analysis/08-drivetrain-as-architecture.md`.*

### 28. `RobotState` and `Superstructure` as components
The two higher seams recovered as instances: `RobotState` is "a sensor that fuses" (an observer);
the superstructure is a component whose `Command_out` feeds subsystems instead of motors. Why a subsystem
and an executive are the *same kind*, why `State` splits into estimate + status above the leaf, and
why every level is named `…State`.
*Sources: `specs/portable-component-model.md` (§3, §5, §10),
`build-spec/subsystems/07-robotstate.md`, `build-spec/subsystems/08-superstructure.md`.*

## K. The dividends and portability

### 29. Telemetry, replay, and tests — the dividends, at every scale
What four loggable PODs per component buy: snapshot every component's channels each tick and you have
AdvantageKit-grade replay and telemetry for the *entire robot at every altitude*, not just motors; a
pure `update` makes every component unit-testable by replaying recorded inputs. The Elite inputs-struct
idea (ch. 3 and 16) generalized from leaves to executives.
*Sources: `specs/portable-component-model.md` (§2, §4), `build-spec/logging.md`,
`build-spec/testing.md`, `build-spec/simulation.md`.*

### 30. Lifecycle and graceful degradation
Baking in the discipline FRC most conspicuously skips (see Lessons from Outside). A real component has a ROS-style
managed lifecycle; health is a field in `State.status`, not an exception; and the `*IONull`
null-object *is* the component in its `fault` state. Degradation becomes a lifecycle transition of the
standard shape rather than a special case bolted on.
*Sources: `specs/portable-component-model.md` (§7),
`corpus-analysis/06-lessons-from-broader-robotics.md` (§5), `alternatives/02-physical-plant-simulation.md`.*

### 31. The ROS bridge and language portability
The proof the factoring is right: the faceplate maps to a ROS 2 node with no impedance mismatch
(Config↔parameters, Command_in↔topic/goal, State↔topic + feedback, Command_out↔published topics,
`update`↔spin). "Keep the message semantics, drop the message transport" — in-process typed calls on
the RIO; a real message only on the one inter-process edge (RIO ↔ coprocessor). The proto3
source-of-truth that makes it language-neutral.
*Sources: `specs/portable-component-model.md` (§8, §11),
`specs/portable-motor-interface.md` (proto3 / ROS bridge).*

## L. Maturity of the proposal

### 32. Open questions and the road to a build recipe
The honest close: the League model is a living proposal, not finished doctrine. Two questions are
now decided (`Observations` is the children's `State` plus the tick timestamp; execution runs
state-up, then commands-down, matching the Elite loop), and the real open ones are named: generic
scheduler vs hand-wired composition, threading against the high-rate odometry queue, the
command-to-goal adapter for WPILib triggers and autos, and the in-loop allocation discipline —
plus the structural gaps the review surfaced (`RobotState`'s dual-graph, the `Subsystem.periodic()`
wrap, splitting `Config` retuning from mode switches). What must close before
`scaffold-robot`/`add-subsystem` emit to this contract by default.
*Sources: `docs/review/portable-component-model-review.md`,
`specs/portable-component-model.md` (Open Questions).*

---

# Part IV — Scoring Elite Code *(the measurement instrument, and the evidence it works)*

*How to score a codebase — yours or anyone's — and trust the number. The rubric, its calibration
against real competition results, and one team's four-year climb.*

### 33. The rubric in full
The eight-dimension instrument, every 0–4 anchor and the grep/AST cheat-sheet, scored directly — plus
the corpus prevalence and cross-validated evidence for *what predicts results and why you must read the
code.* *Source: `rubric/rubric.md`.*

### 34. The San Diego scoresheet
The rubric run on 24 active San Diego teams against season-matched Statbotics EPA: does better code
track winning? Yes — moderately (ρ ≈ 0.55) and unevenly, and the outliers carry the lesson. The full
per-team D1–D8 scoresheet and the per-dimension correlation table. *Sources:
`survey/sd-frc-final-report.md` (+ `*.csv`, inventories).*

### 35. The Patribots, four years
One team (4738) scored season by season with full commit history — a four-season climb 5.0 → 20.0 —
the rubric in motion, and the two rules it illustrates: *rewrite in the offseason*, and *great code
can still carry a four-year zero.* *Source: `examples/patribots-four-year-scoring.md`.*

---

# Appendices

- **Appendix A — How We Developed This.** The method behind Part I, as a five-chapter narrative: how the
  corpus was read (and the *score what's used, not present* rule), the eight-dimension rubric, the
  novice-to-elite maturity ladder, what the architecture actually predicts against competition
  results, and the foundation-first build order. *Sources: `examples/methodology.md`, `rubric/rubric.md`,
  `corpus-analysis/04-novice-to-elite-progression.md`, `survey/sd-frc-final-report.md`,
  `build-spec/elite-architecture.md`.*
- **Appendix B — Glossary and naming decisions.** Faceplate, component, seam, IO line, `u`/`x`,
  estimate vs status, and why *faceplate* replaced the earlier working name *block*. *Sources:
  `specs/portable-component-model.md` (§12), `corpus-analysis/03-io-layer-strategy-pattern.md`.*
- **Appendix C — Source-document crosswalk.** A table mapping every `knowledge/` file to the
  chapter(s) that absorb it, so nothing in the corpus is orphaned by the rewrite.
- **Appendix D — Reviewing for the seams.** The architecture-first code-review checklist: the five seam
  invariants a review protects, S0–S3 severity, principles P1–P10, the deterministic review pass, and
  the auto-fail anti-patterns. *Source: `build-spec/code-review-principles.md`.*

---

# Lessons from Outside *(shelved with the appendices — what the broader field treats as table stakes)*

*Stepping outside FRC to name what the Elite Architecture is still missing. A single survey chapter
today; each lesson will grow its own treatment over time.*

### 1. Lessons from outside FRC
The outside-in view: what ROS / Nav2 / MoveIt / autonomous-driving treat as table stakes that FRC
skips — graceful degradation, lifecycle, process discipline. Sets up Part III by naming what the Elite
Architecture is still missing.
*Sources: `corpus-analysis/06-lessons-from-broader-robotics.md`.*

### 2. Spec-in, code-out — generators against the seam
The spec-in/code-out generators (RobotBuilder, Tuner X, YAGSL, LLMs) scored against the IO seam — all
optimize time-to-drive, not swappability — and the reconciling rule: generate the constants, own the
architecture.
*Sources: `corpus-analysis/07-code-generators.md`.*

---

## Open decisions for the next pass

1. **Part I ↔ Part II overlap is real and intended — keep it honest.** Several components appear in
   both (IO seam: ch. 3 + 16–17; world model: ch. 4 + 20; coordination: ch. 5 + 22–23; drivetrain:
   ch. 6 + 19). The rule is depth: Part I states and motivates, Part II builds. Each Part I seam
   chapter ends with an explicit "deep dive: Part II ch. X" pointer, and Part II does not re-argue
   *why* — only *how*.
2. **Chapter granularity — decided: keep single pages.** Ch. 17, 18, 19, 26, and 27 stay as one
   page each; splitting would churn links for little gain. Revisit only if a page outgrows a
   single sitting.
3. **Coordination as one chapter or two — decided: keep the split.** Ch. 22 is "build this";
   ch. 23 is "know this exists, probably don't build it." Different readers, different registers.
   The full coordination-ladder graphic lives once, at the close of ch. 23.
4. **Tooling scope.** Whether the wiki documents the scoring/scaffolding *tooling* (`analyze-team`,
   `scaffold-robot`, the plugin skills in `AGENTS.md`) or stays purely architectural. Currently out
   of scope.
5. **Chapter numbering — decided: keep the gap.** Chapters 10–14 / section E were absorbed into
   Appendix A; the numbers are reserved so old citations resolve (noted in "How to read it").
