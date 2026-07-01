---
title: 32. Open questions and the road to a build recipe
weight: 32
---
The League model is a living proposal, not finished doctrine, and the honest close to Part III is to
name what is not yet settled. An independent review of the component model found it *conceptually*
ready — the four-channel shape, the pure-function discipline, the fill-pattern taxonomy, and the ROS
lineage all hold, and the motor and swerve specs are genuinely instances of it — while flagging two
load-bearing open questions and three structural gaps that must close before the model can be wired up
and run by default.

## Two load-bearing open questions

**Is `Observations` a fifth channel, or just "the children's `State`"?** The block signature is
`update(Command_in, Observations)`, but the taxonomy table ([ch. 25](25-portable-component-model.md))
has no `Observations` column — and the estimator row exposes the tension, taking observations *in*
while showing no command channel. Observations are not `Command_in` (they are feedback from below, not
intent from above), so the four-channel model implicitly has five channels once you account for the
feedback path. The recommended resolution: a block's `Observations` are simply its **children's most
recent `State`, collected by the outer routing layer** — so `update(Command_in, ChildrensState)` and
the four-channel taxonomy survives without a fifth column. Decide it, and the contract stops being
ambiguous.

**One generic scheduler, or hand-wired composition?** `Command_out` is an array; which child gets which
command? A generic outer loop that topologically sorts blocks and routes `Command_out → Command_in` is
possible and very ROS-like, but for FRC scale the recommended path is **explicit hand-wired composition
in `RobotContainer`** — clearer, debuggable, and consistent with "drop the transport"
([ch. 31](31-ros-bridge-portability.md)). The more useful artifact than a generic scheduler is a *wiring
validator*: a helper that checks every block's `Command_out` has a consumer and every `Command_in` has
a producer.

## Three structural gaps

**Execution order in a tick.** If every block calls `update` once per tick and `Command_out` feeds
children's `Command_in`, the model needs an execution order, and the spec leaves it implicit. Commit to
the **two-pass model**: a top-down command pass (executive → subsystem → motor), then a bottom-up state
pass (motor → subsystem → executive). It is the natural fit for "commands down, state up" and avoids
the one-tick lag a naive single pass introduces.

**`RobotState` is cross-cutting.** "The robot is a tree of blocks" is true for *commands* — they flow
strictly down a hierarchy. State does not. `RobotState` is a peer that the drive and vision write to and
that the executive and other subsystems read from; it is a shared blackboard, not a node in the command
hierarchy ([ch. 28](28-robotstate-superstructure-blocks.md)). The resolution is to **acknowledge the
dual graph explicitly: commands form a tree, state forms a DAG.** Same block contract in both; only the
wiring differs.

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
framework) or *wraps* each block in a WPILib `Subsystem` whose `periodic()` delegates to `update()`,
with the wiring in `RobotContainer.periodic()`. The pragmatic endorsement is the **wrap**: it keeps the
pure-function contract intact while working *with* WPILib, and it is the path a concrete example should
show. Separately, the swerve spec surfaces the single most concrete unbuilt artifact this whole research
produced — a **`TunerConstants → ModuleConstants` adapter** that hands CTRE teams the generator's
numbers without the generator's types.

What must close before the model becomes a recipe — before `scaffold-robot` and `add-subsystem`
([the build tooling](../part-1/07-cross-cutting-practices.md) referenced throughout) emit every
component to this contract by default — is exactly the list above: the `Observations` decision, the
hand-wired-plus-validator choice, the two-pass execution model, the dual-graph acknowledgment, the
`tune`/`reconfigure` split, and the WPILib-wrap example. None of them is conceptual; all of them are the
difference between a design that is right on paper and one a team can run on a real robot in build
season.

That is the honest end of the book. Part I showed the architecture top teams converged on; Part II
opened the hood on each piece; Part III argued that the pieces are one shape and named what naming the
shape buys — telemetry, replay, tests, lifecycle, and language portability at every scale — while being
candid that the recipe is not yet finished. The shape is right. The wiring is the work that remains.
