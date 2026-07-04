---
title: 32. Open questions and the road to a build recipe
weight: 32
---
The League model is a living proposal, not finished doctrine, and the honest close to Part III is to
name what is settled and what is not. An independent review of the component model found it
*conceptually* ready — the four-channel shape, the pure-function discipline, the fill-pattern
taxonomy, and the ROS lineage all hold, and the motor and swerve specs are genuinely instances of it —
while flagging questions the contract could not leave ambiguous. Two of those have since been
**decided**; this chapter records the decisions, then names what genuinely remains open before the
model can be wired up and run by default.

## Two questions, decided

**`Observations` is the children's `State` — not a fifth channel, and not `Command_in`.** The step
signature is `update(Command_in, Observations)`, and the early drafts left the second argument
undefined — the estimator row of the taxonomy exposed the tension, taking observations *in* while
claiming an empty command channel. Decided, as [ch. 25](25-portable-component-model.md) now states: a
component's `Observations` are its **children's (and designated peers') most recent `State`, collected by
the outer wiring layer** and passed as `update`'s second argument, with the tick timestamp riding
along. They are not `Command_in` — observations are feedback from below, not intent from above — so
the four-channel taxonomy survives without a fifth column, and the estimator stops being a special
case: `RobotState`'s `Command_in` is genuinely empty, and everything it consumes is observation.

**Execution order is state-up, then commands-down.** Each tick runs two passes: first a bottom-up
**state pass** — leaves read hardware, and every component's fresh `State` propagates upward — then a
top-down **command pass**, executive to motors, computed against this tick's states. This is Part I's
read → log → decide → actuate loop expressed over the tree: observe first, then act. (Running the
command pass first would decide on *last* tick's states — exactly the one-tick lag the order exists to
avoid.)

## Load-bearing open questions

**One generic scheduler, or hand-wired composition?** `Command_out` is an array; which child gets which
command? A generic outer loop that topologically sorts components and routes `Command_out → Command_in` is
possible and very ROS-like, but for FRC scale the recommended path is **explicit hand-wired composition
in `RobotContainer`** — clearer, debuggable, and consistent with "drop the transport"
([ch. 31](31-ros-bridge-portability.md)). The more useful artifact than a generic scheduler is a *wiring
validator*: a helper that checks every component's `Command_out` has a consumer and every `Command_in` has
a producer.

**Threading.** The signal-synced odometry thread ([ch. 27](27-portable-swerve-interface.md)) samples
at 250 Hz and mutates an inputs struct that a pure 50 Hz `update` is supposed to snapshot. Who owns
the synchronization — the L1 adapter, the wiring layer, a lock-free queue? And what does replay
record: the full 250 Hz sample queue each tick, or only the latest value? The answer decides whether
high-rate odometry lives inside or outside the deterministic boundary, and the model has not given it.

**The command adapter.** The model says the executive receives one `Command_in` per tick, but WPILib
delivers intent as `Trigger` bindings firing `Command` objects, and PathPlanner delivers autonomous
routines as `Command` compositions. Something must adapt those into the executive's `Command_in` — and
must define how an operator override preempts a goal mid-sequence, when a new `Command_in` arrives
while the superstructure is halfway through a legal transition. That adapter is unbuilt and undesigned.

## Two structural gaps

**`RobotState` sits outside the command tree.** "The robot is a tree of components" is strictly true only
of intent, which descends a hierarchy. `RobotState` presents the faceplate but not the tree wiring:
drive and vision feed it, half the robot reads it, and no command edge touches it
([ch. 28](28-robotstate-superstructure-blocks.md)). The resolution is to let the two graphs be
different shapes — intent descends a tree; estimates fan out through a hub, forming a DAG — and make
the wiring layer honest about which edges belong to which graph.

```d2
direction: right
CMD: "Commands — a tree (top-down)" {
  E: Executive
  S1: Subsystem
  S2: Subsystem
  M: Motor
  E -> S1
  E -> S2
  S1 -> M
}
ST: "State — a DAG (many consumers)" {
  DRIVE: Drive
  VIS: Vision
  RS: RobotState
  EXEC: Executive
  AIM: Aim
  DRIVE -> RS
  VIS -> RS
  RS -> EXEC
  RS -> AIM
}
```

**Config versus mode switches.** The boundary test — "changes every loop → `Command`; identifies across
a session → `Config`" — covers the extremes but not the gray middle: things that change *between
matches but not during* (an interlock table, a mechanism toggled on or off). The single
`reconfigure(partialConfig)` door conflates two concerns. Split it: **`tune(partialConfig)`** for
runtime parameter adjustment (gains, limits) that needs no lifecycle change, and
**`reconfigure(partialConfig)`** for structural changes (interlock tables, enabling a mechanism) that
may require a `disable → reconfigure → enable` lifecycle transition.

## The road to a build recipe

Two more questions sit beneath these, both about how the model meets WPILib in practice. A team adopting
it either *replaces* WPILib's `CommandScheduler` with a custom executor (high ceremony, fighting the
framework) or *wraps* each component in a WPILib `Subsystem` whose `periodic()` delegates to `update()`,
with the wiring in `RobotContainer.periodic()`. The pragmatic endorsement is the **wrap**: it keeps the
pure-function contract intact while working *with* WPILib, and it is the path the elevator example of
[ch. 25](25-portable-component-model.md) already sketches. Separately, the swerve spec surfaces the
single most concrete unbuilt artifact this whole research produced — a **`TunerConstants →
ModuleConstants` adapter** that hands CTRE teams the generator's numbers without the generator's types.

What must close before the model becomes a recipe — before `scaffold-robot` and `add-subsystem` (the
build tooling referenced throughout) emit every component to this contract by default — is the open
list above: the hand-wired-plus-validator choice, the threading answer, the command adapter, the
dual-graph wiring, the `tune`/`reconfigure` split, and the WPILib-wrap example — plus one discipline
already decided but not yet demonstrated under load: the allocation rule (plain mutable structs
in-loop, protobuf only at the log-and-wire boundary, [ch. 26](26-portable-motor-interface.md)) held to
through a real 20 ms loop. None of them is conceptual; all of them are the difference between a design
that is right on paper and one a team can run on a real robot in build season.

That is the honest end of the book. Part I showed the architecture top teams converged on; Part II
opened the hood on each piece; Part III argued that the pieces are one shape and named what naming the
shape buys — telemetry, replay, tests, lifecycle, and language portability at every scale — while being
candid that the recipe is not yet finished. The shape is right. The wiring is the work that remains.
