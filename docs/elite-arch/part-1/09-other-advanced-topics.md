---
title: 9. Other advanced topics
weight: 9
---

Where [chapter 8](08-alternatives.md) cataloged the *alternatives* — different ways to build a seam,
with the graph and tree forms taken apart in
[Part II ch. 23](../part-2/23-coordination-graphs-trees.md) — this chapter catalogs the *additions*:
eight techniques that top teams layer onto the elite architecture without restructuring it. Each
attaches at an existing seam, and each earns its place only when the payoff is real. They range from
near-standard on serious swerve to genuinely rare. As in chapter 8, each entry gets what it is, when
it pays off, and where it attaches; the mechanics live in Part II.

## State-space & LQR control

State-space control replaces a hand-tuned PID loop with an optimal controller derived from the
mechanism's physics: model the mechanism as a linear system, compute the feedback gain with a
**Linear-Quadratic Regulator (LQR)**, and estimate the unmeasured state with a Kalman filter. The
draw is principled gains computed from physical constants instead of trial and error, plus an
observer that rejects sensor noise rather than fighting it. It is the rarest technique in this
chapter, because feedforward plus PID gets most mechanisms most of the benefit. It drops in as the
closed-loop controller *inside* a subsystem — below the coordination layer, above the IO line, with
the IO layer unchanged. Mechanics in [the control path](../part-2/15-control-path.md) and
[subsystem archetypes](../part-2/18-subsystem-archetypes.md).

## Swerve setpoint generator

A naive swerve drive commands module states the wheels cannot physically reach within one 50 Hz
tick; the result is skid, degraded odometry, and tipping under hard acceleration. A setpoint
generator clamps each loop's command to the closest feasible one. Drive a swerve robot hard and it
pays for itself immediately — cleaner acceleration, and odometry that stays honest because the wheels
actually track their commands. Originated by 254 and now packaged inside PathPlannerLib (and
spreading elsewhere), it is trending toward standard. It sits between the chassis-speed request and
the module IO calls inside the Drive subsystem;
[the drivetrain subsystem](../part-2/19-the-drivetrain-subsystem.md) carries the details.

## High-frequency threaded odometry

The main loop runs at 50 Hz, but a swerve pose estimate sharpens considerably when a dedicated
thread samples the drive encoders and gyro at 250 Hz (CANivore) / ~100 Hz (RIO CAN bus) and feeds
every timestamped sample into the estimator. Nearly every elite swerve robot collects this benefit —
the pattern is baked into the AdvantageKit swerve template. The thread lives at the boundary between
the drivetrain and the world model, and the sampling stays *below* the IO line, so no vendor type
leaks upward. See [the drivetrain subsystem](../part-2/19-the-drivetrain-subsystem.md) and
[the world model](../part-2/20-the-world-model.md).

## Self-check & fault diagnostics

An operational technique rather than an algorithmic one: a `systemCheck` command drives each
subsystem through a scripted range of motion in the pit, and a fault reporter polls every device's
fault flags and surfaces them on the dashboard before the match. It turns "the robot is acting
weird" into a named, actionable fault a student can fix — rare, which is exactly why it
differentiates: [ch. 7](07-cross-cutting-practices.md) marks it as the top rung of the diagnostics
ladder. It attaches to the lifecycle, running in disabled mode and reading device faults through the
same IO inputs the subsystems already expose (see also
[Part III ch. 30](../part-3/30-lifecycle-degradation.md)).

## Replay as a regression test

AdvantageKit's deterministic replay — feed a recorded match's inputs back through the code and get
identical outputs — is usually framed as a debugging tool, but it doubles as a regression fixture:
check a logged match into the repo, and CI can assert the robot still makes the same decisions after
a refactor. Any team already logging with AdvantageKit has the infrastructure; almost none collects
the dividend ([ch. 7](07-cross-cutting-practices.md)'s point exactly), which makes it a near-free
win. It builds on the same inputs-struct logging as the sim-based tests and attaches to the test
pipeline. The replay mechanics are in [Part II ch. 15](../part-2/15-control-path.md); Part III
[ch. 29](../part-3/29-telemetry-replay-tests.md) generalizes the idea.

## Neural game-piece detection

Beyond AprilTag pose estimation, a neural detector on a Limelight or PhotonVision coprocessor
reports the bearing — and sometimes range — to game pieces, so routines can drive to the best
available target. The detector itself is common among serious teams; the differentiating part is the
architecture on top: drive-to-piece logic that rejects bad detections, filters flicker, and degrades
gracefully when nothing is seen rather than lunging at a phantom. The payoff lands in autonomous and
driver-assist teleop. Architecturally it is just another vision IO — observations crossing the line
as plain numbers, the vendor SDK below it — feeding coordination-layer logic;
[vision systems](../part-2/21-vision-systems.md) has the mechanics.

## Reactive / adaptive autonomy

Most autos are fixed scripts that assume the world cooperates. A reactive auto re-decides on what it
actually senses: skip a pickup when the piece is missing, take the open scoring branch, abort and
reposition rather than stall. In practice it is PathPlanner conditional paths and event markers plus
a small decision layer reading the world model. Over a season, surviving a missed first piece is the
difference between a reliable ten points and an occasional zero. It lives in the coordination layer,
reading [the world model](../part-2/20-the-world-model.md) to branch its command sequence;
[coordination with graphs and trees](../part-2/23-coordination-graphs-trees.md) formalizes the same
ideas.

## QuestNav (VR-headset localization)

A Meta Quest headset is a cheap, extremely good inside-out 6-DOF tracker — it has to be, to render
VR without inducing nausea. QuestNav mounts one on the robot and streams its pose over NetworkTables
as a high-rate, low-drift odometry source fused with AprilTag vision. The newest technique here —
one of the 55 season repos uses it, genuinely emerging across the 2025–2026 seasons — it is worth
carrying where pose accuracy and update rate outweigh the cost and fragility of a consumer headset
on a robot. Architecturally it is one more observation source feeding the same pose estimator: a new
vision IO, with the headset SDK below the line like any other sensor. See
[vision systems](../part-2/21-vision-systems.md) and
[the world model](../part-2/20-the-world-model.md).

---

Adopt these from the seam outward: start from the seam each one attaches to, add it when its payoff
is real for your robot, and let the three-seam foundation carry the weight underneath. That closes
Part I — the baseline, the views, the seams, the practices, the deviations, and the additions.
[Part II](../part-2/) opens the hood.
