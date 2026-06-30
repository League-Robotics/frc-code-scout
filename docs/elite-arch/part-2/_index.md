---
title: Part II — Anatomy of the Elite Architecture
weight: 2
---

# Part II — Anatomy of the Elite Architecture

*The hood comes off.*

[Part I](../part-1/) established what the Elite Architecture is, why to believe it, and how a program
grows into it — at low resolution, deferring every mechanism. Part II is the engineering reference.
Each chapter takes one major component, opens it, and shows the contracts, the decisions, the real
variants in the corpus, and what to build. Code is quoted throughout from the public codebases the
architecture was read from — **to study the technique, not to copy.**

The dividing line with Part I is depth: Part I motivates, Part II builds. Where a Part I chapter named
a seam and pointed here, this is the page it pointed to.

## Chapters

**F. The control path and abstraction**

15. [The control path, end to end](15-control-path.md) — how a teleop or auto command becomes a motor
    voltage, and how state flows back up.
16. [Hardware abstraction and the IO line](16-hardware-abstraction.md) — what the IO seam really is,
    where the control loop sits, and how vendor types leak.
17. [Motor interfaces](17-motor-interfaces.md) — the device-level contract: the reusable `MotorIO`
    shapes the corpus actually uses.

**G. The subsystems**

18. [Subsystem archetypes](18-subsystem-archetypes.md) — the IO quartet per control type, with the
    sim model each uses.
19. [The drivetrain subsystem](19-the-drivetrain-subsystem.md) — the swerve special case: modules,
    kinematics, odometry, and the CTRE-vs-owned-seam spectrum.

**H. Perception and coordination**

20. [The world model](20-the-world-model.md) — `RobotState` and sensor fusion in depth.
21. [Vision systems](21-vision-systems.md) — the pipeline, what teams run, and what it produces.
22. [Coordination I — state machines and the superstructure](22-coordination-state-machines.md) — the
    FSM, the centralized manager, guarded interlocks.
23. [Coordination II — state graphs and behavior trees](23-coordination-graphs-trees.md) — the far end
    of the coordination ladder.
