---
title: 14. Alternatives — legitimate deviations
weight: 14
---
The Elite Architecture is opinionated on purpose — it teaches one foundation-first path so a team can
grow without rewrites. That path is the *default*, not the *only* correct design. This chapter
catalogs the legitimate deviations: patterns that are not the corpus default and not what the build
spec recommends out of the box, but that are sound, defensible, and worth reaching for in the right
situation.

An entry earns its place by being **sound** (not a beginner anti-pattern wearing a clever name),
**uncommon** (if it were the norm it would be in the build spec), **situational** (a real case where
it's the better call *and* a real case where it's over-engineering), and **guard-railed** (it comes
with the conditions that keep it from degrading into the anti-pattern it neighbors). None of these
changes a rubric score; they're a reference for recognizing a pattern and judging whether it was
applied *with* its guardrails or without them.

## Capability-typed devices

The build spec draws the seam at the *subsystem* (`ElevatorIO`). This alternative draws a second,
lower seam at the *device*: interfaces named for a **capability** — `PositionMotor`, `VelocityMotor` —
never a vendor (`ITalonMotor`), with a single hardware object that constructs every device, owns its
configuration, and hands each subsystem the narrow interface it needs. The insight is that once you've
decided a motor's job, you've decided its control strategy, so the *commands* collapse to a
vendor-neutral vocabulary and only *configuration* stays vendor-shaped — so you abstract the command
surface and seal the config inside the implementation.

*Pays off* when several mechanically similar mechanisms can share one implementation, or you have a
real multi-vendor or multi-robot future. *Over-engineering* for a single mechanism where the
subsystem-level seam already says everything. The corpus shows a device-level `MotorIO` in about ten
teams, but almost all leak vendor types; the vendor-clean form is rare, which is why it's an
alternative. It is also the most direct on-ramp to [Part III](../part-3/), whose motor interface is
this idea made portable.

## Physical-plant simulation

`RobotState` is the robot's *estimate* of the world. This alternative materializes its dual: a
**plant** holding the world's *true* state. Settable truth plus a fidelity dial split the simulator
into three independently testable models — dynamics, observation, and estimator — and let a test assert
on **estimation error**, the one thing you can never measure on hardware. The control law stays on one
side of the seam, so nothing is duplicated.

*Pays off* when you want sim to be a test rather than a demo — to prove the estimator converges and the
controller is stable before the robot exists. *Over-engineering* when the sim only echoes setpoints and
no one asserts on it. Both halves already exist unnamed in the corpus (an estimate in 26 teams, truth
models wherever physics forces them); what's missing is the estimate-versus-truth assertion that turns
sim into verification — the D3-high / D4-low gap the rubric flags as the most actionable team finding.

## State-graph coordination

The build spec's superstructure hand-codes the safe transition sequences. This alternative models the
superstructure as a **state graph** and *searches* for a collision-free path — at the far end, A\* over
a discretized configuration space, where "obstacles" are self-collision regions. The prize is
interlocks-as-edge-existence (declare safety once, locally) and verifiable coordination (a graph can be
exhaustively checked that every transition terminates safely, which hand-coded sequences cannot).

*Pays off* when the N² hand-coded transitions get error-prone and you want provable safety; teams
already run anytime A\* on the drivetrain, so this is the same algorithm one layer up. *Over-engineering*
before a team has hit the limits of a finite-state machine. Established but uncommon — 254 is the
corpus's one full instance.

## Behavior trees

The reactive partner to the state graph: a re-ticked tree returning SUCCESS / FAILURE / RUNNING every
cycle, so preemption and recovery fall out of *structure* rather than hand-wired transitions. It is the
game-AI and Nav2 answer to "what do I do *now*," and the natural response to the question a state
machine eventually raises — what happens when the transitions themselves get complicated.

*Pays off* for deeply nested, priority-driven, reactive decision logic. *Over-engineering* before that
complexity is felt. Explicit behavior trees are nearly absent in FRC (3015 is the standout, with a full
runtime and a visual editor), while the command-group cousin (`SequentialCommandGroup`) is universal —
the delta is using it as a top-level *reactive brain* rather than a fixed script.

---

Two of these — capability-typed devices and the plant — point directly at the proposal in
[Part III](../part-3/), where one component shape spans motors, sensors, subsystems, and executives,
and truth-versus-estimate is built into the model. The other two are the D2 ceiling the Elite
Architecture already gestures at. That closes Part I: the architecture, why to believe it, how to grow
it, and where it can legitimately differ. Part II opens the hood.
