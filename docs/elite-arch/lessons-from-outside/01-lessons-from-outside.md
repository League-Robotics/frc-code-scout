---
title: Lessons from outside FRC
weight: 1
---
The Elite Architecture was reconstructed from FRC code, but FRC is a small corner of robotics. Looking
outward shows what the rest of the field treats as non-negotiable — and which of those disciplines
this architecture still skips. The thesis: **FRC independently reinvented the structural core but is
missing most of the runtime and process disciplines.** The seams are spatial (where code lives); the
gaps are temporal (what happens over time, across crashes, across robots, across seasons).

## Where FRC already lands

The broader field splits "robot architecture" into two questions. *How do the pieces talk?* — a
component model, dominantly a graph of components exchanging typed messages (ROS 2, OROCOS, the BRICS
"5 Cs": Computation, Communication, Coordination, Configuration, Composition). *How does the robot
decide?* — a 40-year arc from Sense-Plan-Act through subsumption to the **three-layer hybrid**: a fast
reactive control layer, a slow deliberative planning layer, and an executive that sequences between
them. Modern self-driving stacks are this made concrete (Localization → Perception → Planning →
Control).

In that vocabulary, FRC is a single-process, synchronous, 20 ms system on a known map. The IO seam is
**ports-and-adapters** — exactly what `ros2_control` enforces. `RobotState` is the **observer** half
of control theory's plant–observer split. The `Superstructure` is the **executive layer**. The whole
robot is a degenerate three-layer hybrid with the deliberative layer mostly empty.

Two things the broader field uses that FRC correctly does *not* need, so this stays engineering rather
than mimicry: a multi-process DDS message bus is pure overhead for one RIO plus one coprocessor
(in-process typed interfaces get the decoupling without the transport), and SLAM is unnecessary
because the field ships as CAD months ahead — FRC localization is a known-map problem, which is why
AprilTag pose fusion, not SLAM, is the baseline.

## The seven importable disciplines

| # | Lesson | Outside source | FRC status | Rubric tie |
|---|---|---|---|---|
| 1 | Record-and-replay as a debugging *culture* | `rosbag` (universal) | seam built, dividend uncollected (~1 team) | D5 |
| 2 | Reactive decision-making as the top-level brain | Nav2 behavior-tree navigator | fixed sequences (BT ~1 team) | D2/D6 |
| 3 | Coordination as a *planning* problem | MoveIt / OMPL, A\* | hand-coded interlocks (254 alone) | D2 |
| 4 | Sim-first development + ground-truth testing | Isaac Sim, Gazebo, CARLA | sim mostly echoes setpoints | D3/D4 |
| 5 | Lifecycle + graceful degradation | ROS 2 managed nodes | **no FRC analog** (~2 teams) | D5 |
| 6 | Real-time budgeting as an explicit constraint | OROCOS, WCET | one loop, blocked freely | D1/D3 |
| 7 | Shared, *versioned* interface standards | `ros2_control` | copy-paste between teams | D8 |

Three of these are the highest-leverage gaps. **Replay culture (1)** is the cheapest win — the seam is
already built; the field treats the match log the way ROS treats a bag, the first artifact you reach
for, and robot time is *scarcer* for a school team, which makes replay more valuable in FRC, not less.
**Reactive autonomy (2)** is the biggest competitive unlock — FRC autos are almost universally fixed
sequences, and the real world does not honor a script; the field's answer for decades has been to
decide intent every cycle and let the executive carry it out safely. **Lifecycle and graceful
degradation (5)** is the largest true blind spot with no FRC vocabulary at all: a robot that loses a
camera or browns out a controller mid-match should degrade predictably, not into undefined behavior —
and the structural hook (a null-object IO that reports stale rather than crashing) is one the
architecture already has but rarely uses.

## The generators reward the opposite axis

A whole class of FRC tools takes a spec and hands you robot code — RobotBuilder, CTRE Tuner X's swerve
generator, YAGSL, and the not-yet-real LLM generators. They share one property: **every one optimizes
time-to-driving-robot, which is the opposite axis from the rubric.** The rubric rewards swappability,
sim-testability, and vendor decoupling; the generators reward minutes-to-first-drive. Two of them push
vendor types *above* the seam (Tuner X makes `com.ctre` the drivetrain) or hide the seam inside a black
box you can't trace (YAGSL).

The reconciling move is the practical takeaway and the one elite teams already make: **generate the
constants, own the architecture.** Ingest the generator's tuned numbers — the swerve offsets, the
characterization gains — but keep them behind your own IO seam as files you own, so the vendor stops at
the line. This is the [foundation-first](../appendices/how-we-develop-this/05-foundation-first.md) discipline applied to the tools
themselves.

These gaps — degradation, lifecycle, a versioned interface standard, one shape that spans devices and
executives — are exactly what [Part III](../part-3/) sets out to close. But the corpus also holds sound
patterns that aren't the default and don't fit Part III's single model; [the next
chapter](../part-1/08-alternatives.md) catalogs them.
