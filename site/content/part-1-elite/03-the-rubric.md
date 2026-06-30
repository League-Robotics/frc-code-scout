---
title: 3. Eight dimensions of sophistication
weight: 3
---
The patterns from the corpus become useful only when they become measurable. The instrument is a
rubric of **eight dimensions, each scored 0–4** against anchored, observable indicators, with
half-steps allowed. The full anchors are in [Appendix A](../appendices/a-rubric.md); this chapter is
how to read it.

## The eight dimensions

| | Dimension | The question it asks |
|---|---|---|
| **D1** | Hardware decoupling (architecture) | How far is subsystem logic separated from physical devices? |
| **D2** | Coordination & decision logic | How does the robot decide, and keep mechanisms from fighting? |
| **D3** | Simulation | Can the code run, and surprise you, without the robot? |
| **D4** | Testing & verification | Are there real, run, asserted tests? |
| **D5** | Logging & diagnostics | When the robot misbehaves, how do you know why? |
| **D6** | Autonomous & path planning | Authored paths, optimal trajectories, reactive avoidance? |
| **D7** | Localization & vision | What does the robot believe about where it is? |
| **D8** | Sustainability & process | Will the codebase survive its seniors graduating? |

Each dimension runs the same arc: level 0 is absence, level 1 is the baseline, levels 2–3 are the
real adoption, and level 4 is library-grade. D1 level 4 is a reused generic base, not a repeated one;
D4 level 4 runs whole commands to completion in sim and asserts on the result; D7 level 4 is a
central world model rather than pose estimation bolted onto the drivetrain.

## Why dimensions, not a single ladder score

The maturity ladder ([ch. 10](10-the-maturity-ladder.md)) is right about *sequence within a
dimension* — nobody reaches unit tests without an IO layer, because the IO layer is what makes a
subsystem testable. But teams adopt unevenly *across* dimensions. A team can have a clean IO layer
and zero tests, AdvantageKit logging on top of tangled coordination, or Choreo trajectories driven by
dead-reckoned odometry.

A single sum hides exactly the gap that matters for coaching a team forward: *"you've built the IO
layer — tests are one step away, and you're not taking it."* So the rubric scores each dimension
independently, reports the vector, and reads the **shape** of the profile rather than the total. The
sum is reported; the profile is the finding.

This also corrects the teaching ladder in one place. The progression plan bundles "IO layer +
simulation + lightweight logging" as one leap and "FSM + tests + replay" as another. That is the
right *teaching* order but the wrong *measurement* — in the wild those bundles decompose, so the
rubric splits them.

## Calibrate against prevalence

A marker present in 3 of 55 teams is a ceiling signal; one present in 45 is table stakes. The corpus
index makes this concrete: `commands/`, `Constants`, and `subsystems/` are universal (no signal);
`addVisionMeasurement` appears in 50 teams (pose estimation is the floor, not the ceiling); the IO
interface appears in 24 and a `Superstructure` in 22; and the true ceiling markers — `jgrapht`, a
`WantedState` enum, a behavior-tree runtime, a replay IO variant — appear in one to three teams each.
Reading prevalence keeps a common marker from being mistaken for an achievement.

One caution the corpus forces: hardware implementations are named *by device*, not "Real."
`*IOReal` appears in only about 5 teams, so grepping for it misses most IO layers; the robust signal
is an `interface *IO` with two or more implementations, one of them a sim. The general rule —
[score what's used, not what's present](01-reading-the-corpus.md#the-golden-rule-score-whats-used-not-whats-present)
— applies hardest exactly where naming and presence mislead.

## Reading the profile: common shapes

The vector falls into a handful of recognizable shapes, each with a different highest-leverage next
step:

- **Balanced climber** — all dimensions within ±1. The ladder is working; the next step is whatever
  is lowest.
- **Architecture without verification** (D1 ≥ 3, D3/D4 ≤ 1) — adopted the IO layer's form without its
  payoff, often a copied template. One unit test is the intervention.
- **Tooling adopter** (D5/D6 high, D1/D2 low) — AdvantageScope, PathPlanner, and Choreo on top of
  baseline command code. Tools were installable; architecture was not. An IO layer on one subsystem
  is the intervention.
- **Verification ceiling** (everything ≥ 3 except D4) — the regional-elite profile. Even strong teams
  rarely test, which makes D4 ≥ 2 the clearest signal of real software-engineering culture in the
  whole corpus.

With the baseline and the instrument in hand, the next section describes the architecture the rubric
is measuring — starting with the whole thing [at a glance](04-at-a-glance.md).
