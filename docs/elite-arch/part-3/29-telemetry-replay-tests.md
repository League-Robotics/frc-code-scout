---
title: 29. Telemetry, replay, and tests — the dividends, at every scale
weight: 29
---
This is the chapter that pays for the whole proposal. Part I's cross-cutting practices
([ch. 7](../part-1/07-cross-cutting-practices.md)) hang off the IO seam at the *leaf* — you get
simulation, replay, and tests for a motor because the motor sits behind a data-struct interface. The
block model's payoff is that the *same* dividends now apply at **every altitude**, because every block
— motor, subsystem, estimator, executive — is the same four serializable PODs plus one pure step.

## Why "data, not method calls" is load-bearing

Everything here rests on all four channels being **plain serializable data objects** rather than ad-hoc
method calls. The Elite Architecture already learned this once: every team that builds an IO interface
also builds the logged `Inputs` struct, with no exceptions ([ch. 3](../part-1/03-the-io-seam.md);
[ch. 16](../part-2/16-hardware-abstraction.md) surveys the corpus's variants). The
block model takes that one idea — *the seam is data* — and generalizes it from the leaf to the
executive. Because `Config`, `Command_in`, `State`, and `Command_out` are all data, three capabilities
fall out at once.

## Telemetry and replay, for the whole robot

Snapshot every block's four PODs each tick and you have a complete, structured record of the robot —
not just the motors. The drive subsystem's `SwerveRequest` in and `SwerveDriveState` out, the
superstructure's goal in and per-subsystem goals out, `RobotState`'s observations in and fused pose
out: all of it is captured by the same mechanism, because it is all the same shape.

```d2
direction: down
TICK: "each 20 ms tick"
LOG: "log: Config · Command_in · State · Command_out
for every block, leaf to executive"
TEL: "Telemetry — every channel at every altitude"
REP: "Replay — re-run pure update() over the log"
TICK -> LOG
LOG -> TEL
LOG -> REP
```

This is **AdvantageKit-grade replay and telemetry for the entire robot at every scale**, for the
price of the determinism discipline below. Replay re-runs the recorded `Command_in` + `Observations`
through each block's pure `update` and — provided the code is deterministic and the replay starts from
tick 0 of a complete log ([ch. 25](25-portable-component-model.md)) — gets bit-identical `State` and
`Command_out` back, so a match that misbehaved can be re-examined offline,
at the executive level, not just at the motor. The Elite Architecture collects this dividend only at
the leaf because only the leaf has a data seam; the block model collects it everywhere because every
seam is a data seam.

Replay and telemetry want different slices of that record, and it is worth separating them. **Replay
needs only the boundary**: the leaf observations (what the hardware said) and the top-level commands
(what the driver or auto asked) — everything in between is recomputed by the pure `update`s.
**Telemetry wants the full four-channel snapshot** of every block: logging each intermediate
`Command_out` is what lets you diff a replayed tick against the recorded one to catch nondeterminism,
and what makes the dashboard useful — verification and visibility, not a replay requirement. And the
bit-identical guarantee holds only under a short determinism checklist: no wall-clock reads inside
`update` ([ch. 25](25-portable-component-model.md)), no unlogged randomness, and no dependence on
unordered iteration — a `HashMap` walk that varies run to run is enough to break it.

## Tests, for the whole robot

Because `update` is a **pure function over PODs**, any block is unit-testable by feeding recorded
inputs and asserting on outputs — no hardware, no scheduler, no HAL:

- A **motor block**: feed a `Command`, assert the `MotorState` the sim model produces.
- A **subsystem block**: feed a setpoint and the children's `State`, assert the emitted motor commands
  and `atGoal`.
- The **superstructure block**: feed `SCORE_L4` and a `RobotState` snapshot, assert it emits the legal
  *sequence* of subsystem goals and refuses the illegal ones — the interlock logic, tested in
  isolation, with zero hardware.

That last one is the prize. The coordinator holds the safety-critical sequencing of the robot, and in
the Elite Architecture it is among the least-tested code because there is no clean way to drive it
without the whole robot. As a pure block it is *the* most testable object: its entire contract is
`(State′, Command_out) = update(goal, observations)`, and a test is literally three lines:

```java
var sup  = new Superstructure(CONFIG);
var tick = sup.update(Goal.SCORE_L4, obsWithElevatorDown());          // hand-built or recorded
assertEquals(List.of(ElevatorGoal.RAISE_TO_L4), tick.commandsOut());  // not the arm swing yet
```

This is the same move
that makes `RobotState` the most unit-testable class on the robot ([ch. 4](../part-1/04-the-state-seam.md))
— generalized to every controller above it.

## The discipline that makes it true

The dividend is real only if one rule holds: **emission is a return value, never a side effect**
([ch. 25](25-portable-component-model.md)). The moment a block reaches into a child and calls
`child.setControl(...)`, it is no longer a pure function — you cannot replay it, and a test must stand
up the child to observe what happened. So the testability and the replayability are not separate
features to be added; they are the *same property* (purity) viewed two ways, and they are bought by the
one discipline the model insists on. Build the blocks as pure transforms and you do not "add" logging
or tests later — they are already there, waiting to be collected, at every altitude.

The corpus truth from Part I was that almost everyone builds the leaf seam and almost no one collects
the test and replay dividend even there. The block model's wager is that making the *whole robot* the
same shape changes the economics: when one logging harness and one test pattern cover motor through
executive, the dividend is cheap enough that teams finally take it. The next chapter adds a capability
the shape makes room for but Part I never had — [lifecycle and graceful
degradation](30-lifecycle-degradation.md) — and the chapter after it tests the shape against the
broader field's component model.
