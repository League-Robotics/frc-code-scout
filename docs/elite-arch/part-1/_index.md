---
title: Part I — The Elite Architecture
weight: 1
---

# Part I — The Elite Architecture

*The architecture nobody designed and everybody arrived at.*

No FRC team set out to define a reference architecture. Yet read enough top codebases and the same
shapes appear again and again — a hardware-abstraction seam, a central world model, a coordinator
that turns one goal into many setpoints. Part I introduces that convergent architecture: first the
shared baseline it grows out of, then the whole thing seen from several angles, then each structural
seam in turn, the practices that hang off them, and the legitimate alternatives at the edges.

This part explains **what the architecture is** — at low resolution, the whole board before any one
piece. It does not open the hood; the engineering detail of each component lives in
[Part II](../part-2/). And it does not argue the *method* — how the corpus was read, how to score a
team, and how a program climbs the maturity ladder are gathered in the
[How We Developed This](../appendices/how-we-developed-this/) appendix, so the narrative here can stay on
the architecture itself.

## Chapters

**Orientation**

1. [The baseline and the shape](01-baseline-and-shape.md) — command-based as the shared zero, the two
   joints of coupling, and the two lenses Part I reads the architecture through.
2. [The architecture in five views](02-five-views.md) — the 4+1 view model: the parts and how they
   relate, the libraries they stack on, the 20 ms loop, the hardware schematic, and two scenarios.

**The seams** *(the negative space — the joints between the parts)*

3. [The IO seam — the spine](03-the-io-seam.md) — the Strategy pattern at subsystem granularity.
4. [The state seam — `RobotState`](04-the-state-seam.md) — one fused world model everything shares.
5. [The coordination seam — the superstructure](05-the-coordination-seam.md) — intent vs execution,
   and the six paradigms.
6. [The drivetrain — the special subsystem](06-the-drivetrain.md) — the only actuator that is also
   the primary sensor.

**The practices around the seams**

7. [Cross-cutting practices](07-cross-cutting-practices.md) — simulation, testing, and logging as
   dividends of the IO seam.

**The frontier**

8. [Alternatives](08-alternatives.md) — legitimate deviations, and the bridge to Part III.
9. [Other advanced topics](09-other-advanced-topics.md) — additive techniques that specialize a seam
   rather than replace it: state-space/LQR, swerve setpoint generator, threaded odometry, self-check,
   replay-as-test, neural detection, reactive autonomy, QuestNav.
