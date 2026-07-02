---
title: 2. Eight dimensions of sophistication
weight: 2
---
The patterns from the corpus become useful only when they become measurable. The instrument is a
rubric of **eight dimensions, each scored 0–4** against anchored, observable indicators, with
half-steps allowed. The anchors themselves, the grep/AST cheat-sheet, the measured prevalence table,
and the full catalog of profile shapes all live in one place —
[the rubric in full](../../scoring/33-the-rubric.md). This chapter is the part that page doesn't
carry: where the instrument came from, and why it is shaped the way it is.

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

Each dimension runs the same arc — level 0 is absence, level 1 the baseline, levels 2–3 real
adoption, level 4 library-grade — because the corpus teardown kept finding that arc, dimension after
dimension. The anchors were written by naming what the level *observably looks like* in a repo, not
what it aspires to.

## Why dimensions, not a single ladder score

The instrument did not start as a rubric. It started as the
[maturity ladder](03-the-maturity-ladder.md) — a single ordered climb — and the ladder is genuinely
right about sequence *within* a dimension: the IO layer is what makes a subsystem testable, so tests
cannot precede it. But the moment the ladder met real repos, it broke as a measuring stick, because
teams adopt unevenly *across* dimensions — a clean IO layer with zero tests, AdvantageKit logging on
tangled coordination, Choreo trajectories over dead-reckoned odometry. A single rung number averages
those into mush, and the average hides precisely the fact a coach needs: which adjacent step a team
has already paid for and is not taking.

So the design decision was to score each dimension independently, report the vector, and read the
**shape** of the profile rather than the total. The sum is still reported; the profile is the
finding. The same decision corrected the teaching ladder in one place: the progression plan bundles
"IO layer + simulation + lightweight logging" as one leap and "FSM + tests + replay" as another,
which is the right *teaching* order but the wrong *measurement* — in the wild those bundles
decompose, so the rubric splits them.

## What the pilot changed

Before the full survey, the rubric was piloted on three teams chosen as a deliberate spread —
likely-high, mid, baseline — to test whether it discriminates and surfaces distinct profiles. It
did, and the pilot fixed two scoring rules that the anchors alone underdetermined: **D1 takes the
lenient reading** (a maintained 254-style generic base counts toward the top of D1 even without a
Real/Sim IO swap — generalization is the achievement, not the naming convention), and **D8 credits a
team library that demonstrably exists**, with a note where it is demonstrably consumed. Both calls
are recorded on [the San Diego scoresheet](../../scoring/34-the-san-diego-scoresheet.md), which
inherited them.

## Why the anchors are calibrated against prevalence

An anchor is only meaningful relative to how common its marker is: a structure present in 3 of 55
teams is a ceiling signal, one present in 45 is table stakes, and confusing the two turns the rubric
into either flattery or impossibility. That is why every marker in the cheat-sheet carries its
measured corpus count — the numbers live in
[the prevalence table](../../scoring/33-the-rubric.md#corpus-prevalence-measured). The counts also
guard against naming traps the corpus exposed: hardware implementations are named *by device*, not
"Real," so grepping `*IOReal` misses most IO layers — the robust signal is an `interface *IO` with
two or more implementations, one of them a sim. The general rule —
[score what's used, not what's present](01-reading-the-corpus.md#the-golden-rule-score-whats-used-not-whats-present)
— applies hardest exactly where naming and presence mislead.

Two smaller decisions round out the design. **Equal weighting** is deliberate: an EPA-optimal
re-weighting of the eight dimensions was tested and was not distinguishable from equal weight, so
the sum stays simple. **Half-steps** exist because real teams sit between anchors; the rubric's
scoring rules include an example of a legitimate 2.5 versus a lazy one.

## Reading the profile

Scored vectors fall into recognizable shapes — balanced climber, architecture-without-verification,
tooling adopter, template inheritor, legacy program, verification ceiling — and the shape, not the
sum, determines the highest-leverage next step. The full catalog with its interventions is in
[the rubric in full](../../scoring/33-the-rubric.md#reading-the-profile-common-shapes); the design
point here is simply that the rubric was built so that its *output* is a diagnosis, not a grade.

With the instrument's rationale in hand, the next chapter returns to the ladder the rubric was
carved from — [the novice-to-elite maturity ladder](03-the-maturity-ladder.md).
