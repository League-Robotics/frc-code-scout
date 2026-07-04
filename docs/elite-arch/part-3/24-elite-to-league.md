---
title: 24. From Elite to League — what we keep, what we change
weight: 24
---
Parts I and II reconstructed an architecture that top teams converged on without anyone designing it.
Part III takes the next step: it argues that the architecture is *more uniform than it looks*, and
that naming the uniformity buys things the Elite Architecture leaves on the table. This is the only
prescriptive part of the book. Everything before it described what teams do; from here on we propose
what we'd do, and why.

A note on prerequisites: Part III assumes comfort with Parts I and II — the seams, the corpus
evidence, and the vocabulary they built. It also leans on two outside idioms it does not assume you
know: proto-style schemas ([ch. 26](26-portable-motor-interface.md)) and ROS 2 concepts
([ch. 31](31-ros-bridge-portability.md)). Both are introduced as they are used; passing familiarity
is enough.

## What we keep

The League Architecture is not a replacement. It keeps every commitment Part I earned:

- **The IO seam** — vendor types confined below one interface per device, so logic runs in sim, in
  replay, or against a different motor brand without edits ([ch. 3](../part-1/03-the-io-seam.md)).
- **Intent separated from execution** — a caller requests a goal; a coordinator owns how each
  mechanism reaches it ([ch. 5](../part-1/05-the-coordination-seam.md)).
- **Vendor confinement** — no `com.ctre` / `com.revrobotics` / `org.photonvision` type above the IO
  line, ever.
- **The deferred-dividend discipline** — build the seam first; collect simulation, tests, and replay
  as additions at a known point, never as rewrites ([ch. 7](../part-1/07-cross-cutting-practices.md)).

None of that is in dispute. Part III changes exactly one thing.

## What we change

The Elite Architecture, as Part I presents it, has *three differently shaped seams* — IO, state,
coordination — plus a pile of subsystems, each treated as its own kind of thing. You learn the IO
seam, then separately learn the state seam, then separately learn coordination, then learn how a
drivetrain differs from an elevator. Four shapes, four mental models.

The League claim is that **they are all the same shape, repeated at different altitudes.** A motor, a
sensor, a subsystem, the world-model estimator, and the superstructure are each *the same kind of
object*: something configured once, then advanced each tick by folding an incoming command together
with fresh observations to update its state and emit commands for the things below it. A configured
transfer function with memory. What these components share is not a base class but a **faceplate** —
the same four-channel interface presented at every level ([ch. 25](25-portable-component-model.md)) —
and the proposal is to build to that one contract deliberately rather than rediscovering it
seam by seam.

```d2
direction: right
ELITE: "Elite — four shapes" {
  IO: IO seam
  STATE: state seam
  COORD: coordination seam
  SUBS: subsystems
}
LEAGUE: "League — one faceplate, repeated" {
  EXEC: "Executive"
  S1: "Subsystem"
  S2: "Subsystem"
  M1: "Motor"
  M2: "Motor"
  EXEC -> S1
  EXEC -> S2
  S1 -> M1
  S1 -> M2
}
ELITE -> LEAGUE: "name the common shape"
```

The recursion is the whole idea: a subsystem is a component whose children are motors; a
superstructure is a component whose children are subsystems. The same faceplate describes a leaf
actuator and the robot-wide executive, and the difference between them is not a different base class —
it is *which of the same four channels they populate* ([ch. 25](25-portable-component-model.md)).

## What "portable" buys

The payoff of naming the shape is a single word in the part's title: *portable.* Because every
component presents the same faceplate — four serializable data objects plus one pure step — three
things become free **at every scale**, not just at the motor:

- **Telemetry and replay** for the entire robot — snapshot every component's channels each tick and
  you have AdvantageKit-grade logging from leaf to executive ([ch. 29](29-telemetry-replay-tests.md)).
- **Unit tests** for the entire robot — a pure `update` is testable by replaying recorded inputs, with
  no hardware and no scheduler ([ch. 29](29-telemetry-replay-tests.md)).
- **Language and framework portability** — the faceplate maps cleanly onto a ROS 2 node, which is strong
  evidence the factoring is conventional rather than idiosyncratic ([ch. 31](31-ros-bridge-portability.md)).

And it gives the architecture a place to fix the disciplines FRC most conspicuously skips — graceful
degradation and managed lifecycle ([ch. 30](30-lifecycle-degradation.md)) — once, in the shared shape,
instead of bolting them onto each subsystem.

## The scope, honestly

This is a proposal, not finished doctrine. The motor and swerve interfaces ([ch. 26](26-portable-motor-interface.md),
[ch. 27](27-portable-swerve-interface.md)) are worked all the way down to a proto3 schema; the higher
components ([ch. 28](28-robotstate-superstructure-blocks.md)) are sketched but not yet shipped; and the
model has load-bearing open questions about threading, how driver bindings become commands, and how it
sits on WPILib's scheduler ([ch. 32](32-open-questions.md)). Part III states the shape, shows the instances,
and is candid about what must close before a team can wire it up and run it.

The thesis in one line: **a robot is a tree of components presenting one identical faceplate, and the
kind of component is just which channels it populates.** The next chapter makes that precise.
