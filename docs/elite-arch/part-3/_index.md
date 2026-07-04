---
title: "Part III — The League Architecture"
weight: 3
---

# Part III — The League Architecture

*The Elite Architecture, evolved. Parts I and II's components turn out to be instances of one shape;
naming that shape is the whole proposal.*

Part I reconstructed the architecture top teams converged on; Part II opened the hood on each piece.
Part III is the only **prescriptive** part of the book. It keeps every Elite commitment — the IO seam,
intent separated from execution, vendor confinement, the deferred-dividend discipline — and changes
exactly one thing: it observes that the three differently shaped seams plus the pile of subsystems are
all the **same recursive component**, and proposes building to that one contract deliberately.

What every component shares is its **faceplate**: four serializable data objects plus one pure step.
Naming that shape buys telemetry, replay, tests, lifecycle, and language
portability **at every scale**, not just at the motor. The part states the shape, recovers the motor
and swerve interfaces as its leaf and mid-level instances, and is candid about the open questions that
remain before a team can wire it up and run it.

## Chapters

**I. The unifying idea**

24. [From Elite to League](24-elite-to-league.md) — what we keep, what we change, and what "portable"
    buys.
25. [The Portable Component Model — the faceplate](25-portable-component-model.md) — four channels, one
    pure `update`, the fill-pattern that *is* the taxonomy, and a worked elevator.

**J. The instances**

26. [The portable motor interface](26-portable-motor-interface.md) — the leaf component: two PODs, a
    `oneof` command, capability tiers, a proto3 source of truth.
27. [The portable swerve interface](27-portable-swerve-interface.md) — the mid-level component: five
    layers, one seam, and `ModuleIO` as two motors plus an encoder.
28. [`RobotState` and `Superstructure` as components](28-robotstate-superstructure-blocks.md) — the two
    higher seams recovered as instances; why a subsystem and an executive are the same kind.

**K. The dividends and portability**

29. [Telemetry, replay, and tests — the dividends, at every scale](29-telemetry-replay-tests.md) — the
    inputs-struct idea generalized from leaves to executives.
30. [Lifecycle and graceful degradation](30-lifecycle-degradation.md) — health as state, the null
    component as the fault state.
31. [The ROS bridge and language portability](31-ros-bridge-portability.md) — keep the message
    semantics, drop the transport.

**L. Maturity of the proposal**

32. [Open questions and the road to a build recipe](32-open-questions.md) — the decisions now on the
    record, the questions still open, and what must close before the generators emit to this
    contract.
