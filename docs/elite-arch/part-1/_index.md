---
title: Part I — The Elite Architecture
weight: 1
---

# Part I — The Elite Architecture

*The architecture nobody designed and everybody arrived at.*

No FRC team set out to define a reference architecture. Yet read enough top codebases and the same
shapes appear again and again — a hardware-abstraction seam, a central world model, a coordinator
that turns one goal into many setpoints. Part I reconstructs that convergent architecture from the
evidence: how the corpus was read, what recurs, how to measure it, how a program grows into it, and
whether any of it correlates with winning.

This part explains **what the architecture is** and **why it's worth believing**. It does not open
the hood — the engineering detail of each component lives in [Part II](../part-2/). The dividing line
is depth: Part I states and motivates; Part II builds.

## Chapters

**A. Method and instrument**

1. [How we read the corpus](01-reading-the-corpus.md) — the study, end to end, and the one rule that
   makes its findings trustworthy.
2. [The baseline everyone starts from](02-the-baseline.md) — WPILib command-based, and why
   modularity is a ladder rather than a binary.
3. [Eight dimensions of sophistication](03-the-rubric.md) — the rubric: what it measures and how to
   read a profile.

**B. The architecture and its seams**

4. [The architecture at a glance](04-at-a-glance.md) — the whole thing in one sitting: three seams,
   goal-down/state-up, build-the-seams-defer-the-payoffs.
5. [The IO seam — the spine](05-the-io-seam.md) — the Strategy pattern at subsystem granularity.
6. [The state seam — `RobotState`](06-the-state-seam.md) — one fused world model everything shares.
7. [The coordination seam — the superstructure](07-the-coordination-seam.md) — intent vs execution,
   and the six paradigms.
8. [The drivetrain — the special subsystem](08-the-drivetrain.md) — the only actuator that is also
   the primary sensor.

**C. The practices around the seams**

9. [Cross-cutting practices](09-cross-cutting-practices.md) — simulation, testing, and logging as
   dividends of the IO seam.

**D. Growth and proof**

10. [The novice-to-elite maturity ladder](10-the-maturity-ladder.md) — the five-season climb,
    sequenced by pain.
11. [What the architecture predicts](11-what-it-predicts.md) — the validation against competition
    results, honestly.

**E. Synthesis and frontier**

12. [Foundation-first](12-foundation-first.md) — the build order, the deferred dividends, and the one
    rule that carries it all.
13. [Lessons from outside FRC](13-lessons-from-outside.md) — what the broader field treats as table
    stakes that FRC skips.
14. [Alternatives](14-alternatives.md) — legitimate deviations, and the bridge to Part III.
