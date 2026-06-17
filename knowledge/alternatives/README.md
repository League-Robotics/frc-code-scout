# Alternatives

Uncommon-but-good architecture ideas: patterns that are **not** the corpus default and **not** what
`build-spec/` recommends out of the box, but that are sound, defensible, and worth reaching for in the
right situation.

The build spec is opinionated on purpose — it teaches one foundation-first path (the three seams) so a
team can grow without rewrites. That path is the *default*, not the *only* correct design. This directory
holds the legitimate deviations: ideas that a thoughtful team might adopt instead of, or alongside, the
canonical pattern, with a clear statement of **why**, **when it pays off**, and **when it doesn't**.

## What earns a place here

An entry belongs in `alternatives/` if it is:

- **Sound** — it holds up to scrutiny; it is not a beginner anti-pattern wearing a clever name.
- **Uncommon** — most of the corpus doesn't do it (if it were the norm it would live in `build-spec/`).
- **Situational** — there is a real, nameable situation where it is the better call, *and* a real situation
  where it is over-engineering. Every entry must be honest about both.
- **Guard-railed** — it comes with the conditions that keep it from degrading into a known anti-pattern.

## How these relate to the rubric and build spec

These are not rubric dimensions and they do not change a score. When `audit-architecture` or `analyze-team`
meets a codebase that uses one of these patterns, this directory is the reference for recognizing it and
judging whether it was applied *with* its guardrails (good) or *without* them (the anti-pattern it
neighbors). Treat `build-spec/` as canon and `alternatives/` as "also legitimate, for these reasons."

## Entries

- `01-capability-typed-devices.md` — device-level motor/sensor interfaces named by **capability, not
  vendor** (`PositionMotor`, not `ITalonMotor`), assembled by a single **hardware object** below the IO
  line. An alternative seam to the build spec's subsystem-level `XxxIO`; pays off with mechanism reuse and
  a genuine multi-vendor / multi-robot future.
- `02-physical-plant-simulation.md` — materialize the robot's **true** state as a first-class **plant**,
  the dual of `RobotState` (truth vs. estimate). Settable truth + a fidelity dial split the simulator into
  three independently-testable models (dynamics, observation, estimator); keeps the control law on one side
  of the seam so nothing is duplicated. Builds on doc 01's hardware object, which owns the plant.
- `03-state-graph-coordination.md` — *(sketch)* coordination as **graph search**: model the superstructure
  as a state graph and search the safe transition path instead of hand-coding N² sequences; at the far end,
  **A\*** over a discretized configuration space. Established but uncommon in FRC (254 is the corpus's one
  full instance). Extends the build-spec superstructure seam (D2).
