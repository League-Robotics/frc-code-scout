> **Archived — absorbed into the elite-arch wiki.** See Lessons from Outside ch. 1 (`docs/elite-arch/appendices/lessons-from-outside/01-lessons-from-outside.md`). Retained here for historical reference.

# Lessons From Broader Robotics — What FRC Should Import From the Field at Large

*How professional, academic, and industrial robotics structure code — and which of their
practices FRC treats as exotic or skips entirely. The thesis: FRC independently reinvented the
**structural** core (the IO seam is ports-and-adapters), but is missing most of the **runtime and
process** disciplines the rest of the field considers non-negotiable. The seams are spatial —
where code lives. The gaps are temporal — what happens over time, across crashes, across robots,
across seasons.*

> **Status:** synthesis doc, not a build-out. Each lesson below is established practice *outside*
> FRC, mapped onto the seams in `../build-spec/elite-architecture.md` and the deviations in
> `../alternatives/`. Several of these already have a partner doc that develops the FRC form
> (behavior trees `04`, state-graph coordination `03`, the plant `02`); this doc is the outside-in
> view that motivates them and adds the ones with no FRC partner yet (lifecycle/degradation,
> real-time budgeting, interface standardization). Where a claim rests on the broader-robotics
> literature, the source is in **Pointers**.

---

## 0. How the rest of the field structures robot code (the 60-second map)

Two questions get conflated under "robot architecture," and the outside world answers them with
separate bodies of work:

1. **How do the pieces talk?** — *middleware / component model.* The dominant answer is a **graph
   of independent components exchanging typed messages**: ROS 2 (nodes over DDS pub/sub, plus
   services and actions), and its relatives OROCOS (hard real-time industrial control), YARP
   (humanoid/cognitive, runtime-pluggable transports), MOOS (marine, star topology through a
   central DB), LCM (a stripped-down low-latency bus). The academic articulation is the **"5 Cs"**
   (BRICS): separate **C**omputation, **C**ommunication, **C**oordination, **C**onfiguration,
   **C**omposition.
2. **How does the robot decide what to do?** — *control paradigm.* A 40-year arc: **Sense-Plan-Act**
   (1960s, failed — planning too slow, acted on stale data) → **subsumption / reactive** (Brooks
   1986, layered behaviors, no world model) → **three-layer hybrid** (the reconciliation, still the
   default: a fast reactive control layer, a slow deliberative planning layer, an executive that
   sequences between them). Modern autonomous-driving stacks (Autoware, Apollo) are this made
   concrete: **Localization → Perception → Planning → Control.**

**What FRC is, in that vocabulary.** A single-process, synchronous, 20 ms-periodic system on a
known map. The IO seam is **ports-and-adapters** (Cockburn) / a per-subsystem **HAL** — exactly
what `ros2_control` enforces with its hardware-interface abstraction. `RobotState` is the
**observer/estimate** half of control theory's plant–observer split (`../alternatives/02`).
`Superstructure` is the **executive layer**, implemented as an FSM. The whole robot is a degenerate
**three-layer hybrid** with the deliberative layer mostly empty.

**What FRC correctly does *not* need** (so this doc doesn't cargo-cult): the multi-process DDS
message bus is pure overhead for one RIO + one coprocessor — in-process typed interfaces and
dependency injection get the decoupling without the transport (see `03-io-layer-strategy-pattern.md`).
And **SLAM / map-building is unnecessary**: the field geometry ships as CAD months ahead, so FRC
localization is a *known-map* problem, which is why AprilTag pose fusion — not SLAM — is the corpus
baseline (`addVisionMeasurement` in 50/55 teams). Importing DDS or SLAM would be mimicry, not
engineering. The lessons worth taking are the runtime disciplines (§1–§6) and the ecosystem
discipline (§7).

---

## The seven importable lessons

Ranked roughly by leverage for a strong-but-not-elite team. The corpus numbers throughout are from
`data/code-index.duckdb` (55 season repos) and match the prevalence tables in `../rubric/rubric.md`
and `elite-architecture.md`.

| # | Lesson | Outside-field source | FRC status (corpus) | Rubric tie |
|---|---|---|---|---|
| 1 | Record-and-replay as a debugging *culture* | `rosbag` (universal in ROS) | seam built, dividend uncollected (~1 team) | D5 |
| 2 | Reactive decision-making as the top-level brain | Nav2 behavior-tree navigator | fixed sequences (BT ~1 team) | D2/D6 |
| 3 | Coordination as a *planning* problem | MoveIt / OMPL, A* / RRT | hand-coded interlocks (A* superstructure: 254 alone) | D2 |
| 4 | Sim-first development + ground-truth testing | Isaac Sim, Gazebo, CARLA | sim mostly echoes setpoints | D3/D4 |
| 5 | Lifecycle management + graceful degradation | ROS 2 managed nodes, Nav2 lifecycle manager | **no FRC analog** (FaultReporter ~2 teams) | D5 |
| 6 | Real-time budgeting as an explicit constraint | OROCOS RTT, ROS 2 executors, WCET | one loop, blocked freely | D1/D3 |
| 7 | Shared, *versioned* interface standards | `ros2_control` robot-agnostic controllers | copy-paste between teams | D8 |

---

## 1. Record-and-replay is a debugging *culture*, not a feature

In ROS, `rosbag record` → replay is the first thing a roboticist learns: record everything, always,
and debug **off-robot** by replaying recorded reality. **AdvantageKit is a near-direct port of this
idea into FRC** — deterministic re-execution of your actual code against the actual logged inputs
(`../build-spec/simulation.md`, `elite-architecture.md` §5.D).

The lesson is not "adopt AdvantageKit" — the build spec already teaches that. It is the **mindset**:
the broader field does not debug live on hardware; it debugs against a recording. And the economics
are *inverted* in FRC's favor — robot-access time is scarcer for a school team than for a funded
lab, which makes replay **more** valuable in FRC, not less.

> **Corpus reality check.** The IO seam that makes replay free exists in 24 teams (44%), and *every*
> IO team has the `Inputs` struct replay consumes (0 exceptions). Yet a replay IO variant appears in
> **~1 team**. The seam is built and the dividend is left on the floor — the single clearest
> "form without payoff" gap in the corpus, and the cheapest to close because no new subsystem code
> is required (just the `REPLAY` run mode, already wired in the build spec).

**The import, concretely:** treat the match log the way ROS treats a bag — the primary artifact you
reach for when something went wrong, not an afterthought. Replay-as-test (`other-topics.md`) is the
same move turned into a regression suite.

---

## 2. Reactive decision-making as the top-level brain

This is the **largest genuine hole**. Nav2 made the **behavior tree the standard orchestration
layer** for mobile robots: a re-ticked tree where the root selector re-evaluates priorities every
cycle, so preemption and recovery fall out of *structure* rather than hand-wired transitions
(`../alternatives/04` develops the FRC form and the WPILib command-group correspondence).

FRC autonomy is almost universally **fixed sequential routines**: `SequentialCommandGroup` in 49
teams, parallel groups in 37, `Conditional`/`SelectCommand` in 23 — but an explicit reactive
top-level tree in **~1 team** (3015). The building blocks are everywhere; using them as a
**reactive brain** is the unexplored part.

The broader field abandoned scripted sequences for reactive policies decades ago for one reason:
**the real world does not honor a script.** A defended game piece, a missed intake, a bumped
trajectory — a three-piece auto that fails on contact is the *same brittleness* SPA hit in 1985,
and the answer is the same one Brooks and then Nav2 reached. `../alternatives/04` poses the open
question ("true BT brain, or the command-based 80% + a reactive root tick?"); the outside-field
answer is unambiguous: **run a reactive root tick.** Decide intent every cycle, then let the
Superstructure (FSM or graph, §3) execute it safely. *BT decides intent; the coordinator executes it.*

---

## 3. Coordination is a *planning* problem, not a wiring problem

Outside FRC, "don't let the arm hit the elevator" is **motion planning over configuration space** —
declare the obstacles once, then *search* for a collision-free path (MoveIt + OMPL; A* for low-DOF,
RRT/PRM sampling planners for high-DOF). FRC instead hand-codes the N² (from → to) transition
sequences, gets them subtly wrong, and scatters interlocks as `if` checks across subsystems.

`../alternatives/03` already has this exactly right, including the framing that makes it land:
**you already run anytime-dynamic A* on the drivetrain** (PathPlanner `LocalADStar` / `pathfindToPose`,
35 corpus teams) — the superstructure is the *same algorithm in joint space*, searching
`(elevatorHeight, armAngle, wristAngle)` where "obstacles" are self-collision regions.

> **Corpus reality check.** `Superstructure` coordinator ≈ 22–28 teams (the dominant pattern);
> state-machine / `RobotManager` FSM ≈ 17; named-state enums ≈ 34; explicit state-graph types in
> ~5 teams (190, 254, 2910, 3476, 5026); genuine **A* over the superstructure in effectively 254
> alone**. Meanwhile A*-family planning *on the drivetrain* is in 35 teams. Teams accept graph
> search on the field plane and reject it one layer up out of unfamiliarity, not difficulty.

The prize is **interlocks-as-edge-existence** (declare safety once, locally) plus **verifiable
coordination** — a graph can be exhaustively tested that every (from, to) path is collision-free and
terminates, which hand-coded transitions cannot.

---

## 4. Sim-first development with ground-truth testing

Autonomous-driving and industrial stacks develop in **simulation first** and validate against
**known ground truth** — the premise of Isaac Sim, Gazebo, and CARLA. The defining move is control
theory's **plant–observer split**: hold true state and the estimate *simultaneously* and assert on
**estimation error**, which is impossible on hardware. `../alternatives/02` materializes exactly
this (the settable-truth plant as the dual of `RobotState`).

FRC simulation is mostly D3-level-1 — `simulationPeriodic` echoing setpoints. The lesson from the
broader field: simulation's job is to **surprise you and fail your tests** before the robot exists.
The prerequisites the outside world treats as routine — separable dynamics / observation / estimator
models, settable ground truth, a fidelity dial — are standard everywhere except FRC, where
`../alternatives/02` notes nobody even names the duality.

> **Corpus reality check.** Both halves already exist, unnamed: a `RobotState` *estimate* in 26
> teams; *truth* models where physics forces them — per-device WPILib plants (`ElevatorSim` etc.)
> in 40, the CTRE sim bridge in 27, **maple-sim** central true-state world in 16, PhotonVision sim
> (a sensor observing true pose with error) in 29. The pieces are present; the **estimate-vs-truth
> assertion** — the thing that turns sim into a test instead of a demo — is what's missing. This is
> the D3-high / D4-low asymmetry the rubric flags as the single most actionable team finding.

---

## 5. Lifecycle management and graceful degradation

The lesson with **no FRC analog at all.** ROS 2 **managed (lifecycle) nodes** carry explicit
bringup/teardown state machines; Nav2's **lifecycle manager** uses bond connections to detect a
crashed node and *deterministically transition the system down* rather than fail into undefined
behavior. The broader field treats "what happens when a sensor drops out or a process dies
mid-mission" as a first-class architectural concern (see also the ROS fault-tolerance literature).

FRC's closest embryo is the self-check / `FaultReporter` pattern (D5 level 4, ~2 teams). A robot
that loses a camera or a CAN device mid-match should **degrade predictably** — fall back to a known
safe behavior, flag the fault, keep the rest of the robot running — not behave undefined. Every
team has lived the failure mode (a Limelight reboots, a SPARK browns out, the pose jumps); almost
none have an *architecture* for it.

**The import:** a defined degradation policy per seam. At the IO seam, a `*IONull` / null-object
implementation (real but near-absent in the corpus) is the structural hook — a dropped device swaps
to a no-op that reports stale/invalid rather than crashing the loop. At the state seam, vision
rejection logic (per-tag std-devs, outlier rejection) is graceful degradation FRC *does* partly do
(D7 L3) — generalize the instinct to every input.

---

## 6. Real-time budgeting as an explicit constraint

OROCOS exists because hard-real-time control treats the loop period as a **contract with a
worst-case execution time (WCET)**, not a suggestion; ROS 2's executor model and DDS QoS were
redesigned for the same reason. FRC stuffs everything into one 20 ms loop and then **blocks it** —
a `Thread.sleep`, a synchronous vision round-trip, a heavy path recompute — and watches the loop
overrun and the watchdog fire.

The importable discipline is simple and almost never taught in FRC: **know your loop budget, measure
it, and move high-frequency or blocking work off the main thread.** Threaded high-frequency odometry
(`other-topics.md` lists it as an *advanced* technique) is the broader field's **default** posture —
sensor acquisition runs on its own timer, the control loop consumes the latest sample. The 20 ms
loop is a real-time scheduler with one thread; the field's lesson is to treat it like one.

---

## 7. Shared, *versioned* interface standards across robots

`ros2_control`'s entire point: the **same controller runs on any robot** because hardware sits
behind standardized state/command interfaces (Actuator / Sensor / System). The broader field has a
**package ecosystem**; FRC has **copy-paste between teams**.

`05-motor-io-interfaces.md` already catalogs the six reusable `MotorIO` contracts in the corpus and
proposes a unified one — which is precisely the `ros2_control` move. The field-level lesson is that
**standardization plus versioning** (a shared `MotorIO` contract consumed as a dependency, not
forked) is what turns individual cleverness into compounding community capability.

> **Corpus reality check.** `MotorIO`-style generalization and a carried-across-seasons `lib/`
> appear in ~half the corpus (`util/` 36, `lib/` 26), and the season-independent library pattern
> (`SuperCORE`, `WarlordsLib`, `3128-common`, `NOMADBase`) is the D8 L3 marker. But these are
> almost always **forked/copy-pasted, not versioned and consumed** (D8 L4, rare). The gap between
> "we have a lib folder" and "we publish a versioned dependency other robots consume" is the same
> gap ROS closed with its package index — and the one keeping FRC reuse local instead of cumulative.

This is also the **clean-vendor-confinement** problem one level up: of 24 IO-seam teams, 22 still
import `com.ctre` / `com.revrobotics` above the line. A standardized, lint-enforced interface
boundary is what makes the abstraction portable rather than aspirational (`elite-architecture.md` §6).

---

## What this implies for the rubric and the build spec

- **D2** should recognize the reactive-brain (§2) and planning-based (§3) coordination tiers as the
  L4 ceiling they already gesture at ("transition logic as data") — and the build spec could add a
  reactive-root-tick scenario alongside the guarded-transition one in §5.B.
- **D5** under-weights the *operational* half — replay actually exercised (§1) and fault/degradation
  reporting (§5). The latter has no rubric vocabulary yet; it's the clearest expansion candidate.
- **D3/D4** already encode the sim-first gap (§4) as the D3-high/D4-low asymmetry; the plant doc is
  the build-out.
- **D8** captures library *existence* but not the **versioned-consumption** standard (§7) that
  separates local reuse from ecosystem reuse — the L3→L4 distinction could lean harder on it.

## Leverage ranking (for a typical strong-but-not-elite team)

1. **Replay culture (§1)** — cheapest win; the seam is already built.
2. **Reactive autos (§2)** — biggest competitive unlock.
3. **Lifecycle / graceful degradation (§5)** — largest true blind spot, no existing FRC vocabulary.

Then coordination-as-planning (§3) and ground-truth sim testing (§4) for teams already at the
ceiling, with real-time budgeting (§6) and interface standardization (§7) as the program-grade
maturity markers.

---

## Pointers

**Middleware / component models**
- ROS 2 architecture & design patterns — *Programming Multiple Robots with ROS 2* (OSRF):
  https://osrf.github.io/ros2multirobotbook/ros2_design_patterns.html
- `ros2_control` hardware abstraction (state/command interfaces, Resource/Controller Manager):
  https://control.ros.org/master/doc/ros2_control/hardware_interface/doc/hardware_components_userdoc.html
- Robotics middleware survey (OROCOS / YARP / MOOS / LCM): https://en.wikipedia.org/wiki/Robotics_middleware
- The "5 Cs" / BRICS component model — separation of Computation, Communication, Coordination,
  Configuration, Composition.

**Control paradigms**
- Kortenkamp, Simmons & Brugali, *Robotic Systems Architectures and Programming* (Springer Handbook):
  https://www.cs.cmu.edu/~reids/papers/Robot_Architectures.pdf — the SPA → subsumption → three-layer arc.
- Brooks, "A Robust Layered Control System for a Mobile Robot" (1986) — subsumption.

**Reactive decision-making (§2)**
- Colledanchise & Ögren, *Behavior Trees in Robotics and AI*.
- Nav2 behavior-tree navigator: https://docs.nav2.org/behavior_trees/index.html ; BehaviorTree.CPP + Groot.

**Coordination as planning (§3)**
- Lozano-Pérez, configuration-space motion planning; MoveIt / OMPL (sampling planners).
- Drivetrain analogue: PathPlanner `pathfindToPose` / `LocalADStar`. Corpus instance: 254's `AStarSolver`.

**Sim-first + ground truth (§4)**
- NVIDIA Isaac Sim, Gazebo, CARLA as sim-first development environments.
- Production precedent in-corpus: maple-sim (`SimulatedArena`/`SwerveDriveSimulation`), PhotonVision `VisionSystemSim`.

**Lifecycle & fault tolerance (§5)**
- ROS 2 managed/lifecycle nodes; Nav2 lifecycle manager + bond connections: https://docs.nav2.org/concepts/index.html
- ROS fault-tolerance literature (e.g. "ROS Rescue").

**Autonomous-driving stacks (the three-layer hybrid, concretely)**
- Autoware vs Apollo comparison (Localization / Perception / Planning / Control): https://arxiv.org/abs/2501.18942

## See also (internal)

- `../build-spec/elite-architecture.md` — the three seams these lessons attach to.
- `../alternatives/02-physical-plant-simulation.md` — the build-out of §4 (plant/observer duality).
- `../alternatives/03-state-graph-coordination.md` — the build-out of §3 (coordination as graph search).
- `../alternatives/04-behavior-trees.md` — the build-out of §2 (reactive top-level brain).
- `03-io-layer-strategy-pattern.md` — why the IO seam is ports-and-adapters (the structural core FRC already has).
- `05-motor-io-interfaces.md` — the unified `MotorIO` contract proposal (the FRC form of §7).
- `../rubric/rubric.md` — D2, D5, D8 are where these lessons land.

## Open question for a deeper build-out

Of the seven, three have no FRC partner doc yet — **graceful degradation (§5)**, **real-time
budgeting (§6)**, and **versioned interface standardization (§7)**. §5 is the strongest candidate for
its own `alternatives/` build-out: it has a real, universal failure mode, an established outside-field
solution (managed nodes + bond-based fault detection), a structural hook already in the build spec
(the `*IONull` null-object), and no existing FRC vocabulary. Decide whether to promote it before
writing it out.
