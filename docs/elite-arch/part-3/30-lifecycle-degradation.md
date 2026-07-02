---
title: 30. Lifecycle and graceful degradation
weight: 30
---
The [Lessons from Outside](../appendices/lessons-from-outside/01-lessons-from-outside.md) survey names
graceful degradation as the discipline FRC most conspicuously skips: a wire comes loose, a CAN device
drops, and baseline robot code either crashes or sails on commanding a motor that isn't there. ROS,
Nav2, and the autonomous-driving stack treat managed lifecycle and health as table stakes. The block
model is the right place to fix this once — in the shared shape — instead of bolting a special case
onto each subsystem.

## A real component has a lifecycle

A block is not just "construct it and call `update` forever." Modeled on ROS 2 managed nodes — with
two deliberate deviations, named below — it moves through defined states:

```d2
direction: right
C: constructed
CF: configured
E: enabled
R: running
D: disabled
F: fault / degraded
C -> CF: configure(Config)
CF -> E: enable
E -> R: tick
R -> D: disable
D -> E: re-enable
R -> F: device lost
F -> R: recovered
```

The deviations are improvements for FRC, not inheritance. ROS 2's primary states are Unconfigured /
Inactive / Active / Finalized, and errors route through a *transitional* `ErrorProcessing` state —
there is no persistent fault or degraded primary state. We add one, because an FRC mechanism can lose
a device mid-match and must keep ticking in that condition for minutes, not merely transition through
it. And we split ROS 2's single Active into `enabled` / `running`, matching the field-management
reality that a robot is powered and configured well before it is allowed to move. Within the fault
box, `fault` means total loss — the device is gone, emit safe zeros — while `degraded` means impaired
but still acting: one motor of a pair lost, a reduced current budget, still pursuing its command.

The transitions are the same for every block, so the discipline is written once and inherited by motor,
subsystem, estimator, and executive alike. A block that is `configured` but not `enabled` holds its
parameters but commands nothing; a block in `fault` accepts commands but emits only safe ones. None of
this is mechanism-specific.

## Health is a field, not an exception

The first concrete requirement: **a `connected` / health field lives in `State.status`, not in an
exception path.** The corpus already does this at the leaf without naming it — the swerve `ModuleIO`
inputs carry `driveConnected` and `turnConnected`, and CTRE's drive state carries `FailedDaqs`. The
block model promotes that from a leaf convention to the universal rule: every block reports its health
*as part of the state it already exposes*. A parent reads a child's `State.status` the same way it
reads the estimate, so "the elevator's left motor is disconnected" propagates up the tree as ordinary
state, available to the superstructure's interlock logic, the telemetry log, and the driver dashboard
through one path — not as an exception that some layer must remember to catch.

## The null block *is* the fault state

The second requirement makes degradation structural rather than ad-hoc. The Elite Architecture already
has the right object: the `*IONull` null-object ([ch. 16](../part-2/16-hardware-abstraction.md)), a do-nothing
implementation whose methods are deliberately empty so a subsystem with disconnected hardware runs as a
safe no-op instead of crashing. In the block model, **the null implementation is the block in its
`fault` lifecycle state**: it accepts commands, emits safe/zero outgoing commands, and reports
`connected = false`.

That reframing matters. Degradation stops being a special code path bolted on after the fact and
becomes **a lifecycle transition of the standard shape**: a block detects a lost device, transitions
`running → fault`, and its behavior in that state is simply "be the null block." Because the null block
satisfies the same contract as the real one, nothing above it needs a branch for the degraded case —
the executive keeps issuing goals, the failed block keeps reporting `connected = false` and emitting
zeros, and the rest of the robot keeps running. A robot that loses a non-critical mechanism mid-match
degrades to operating without it instead of faulting the whole program.

## Why the shape is the right home for it

Graceful degradation is hard to retrofit precisely because, in a baseline architecture, every
subsystem handles failure its own way — or doesn't. By making every active thing the same block with
the same lifecycle and the same `State.status` health field, the model gives degradation *one*
definition that every component inherits. This is the structural hook the outside-robotics survey asked
for: not a library to import, but a property of the shared shape. The discipline FRC skips becomes the
default, because there is nowhere else for it to live.

The shape also has one more thing to prove — that it is genuinely the same factoring the broader field
uses, not a coincidence. The next chapter cashes that in: [the ROS bridge and language
portability](31-ros-bridge-portability.md).
