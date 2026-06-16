---
title: Home
layout: home
nav_order: 1
---

# Inside Competition Robot Code

**A field guide to FRC robot software — what sophisticated student code looks like, how to grade
it, and how to build it.**

This is a book in five parts, derived from reading the public codebases of dozens of top FRC teams,
turning the recurring patterns into an 8‑dimension rubric, validating that rubric against real
competition results, and distilling it into a foundation‑first architecture you can build without
rewrites.

## Start here

- **[The Rubric]({% link book/rubric/rubric.md %})** — the eight dimensions (D1–D8) of code
  sophistication, with anchored indicators and measured corpus prevalence. Read this first to grade
  any team's code.
- **[The Build Spec]({% link book/build-spec/index.md %})** — the architecture itself. Begin with
  **[Elite Architecture]({% link book/build-spec/elite-architecture.md %})** (the three seams), then
  the per‑subsystem build guides starting at
  **[Anatomy of a Subsystem]({% link book/build-spec/subsystems/00-anatomy-of-a-subsystem.md %})**.

## The five parts

1. **Rubric** — the scoring instrument.
2. **Corpus Analysis** — why the rubric looks the way it does (the national 37‑team survey, the IO
   layer as the Strategy pattern, the novice→elite ladder).
3. **Build Spec** — the elite architecture: the IO seam, `RobotState`, and `Superstructure`; a deep
   dive per subsystem archetype; and the cross‑cutting practices (testing, simulation, logging).
4. **Survey** — how San Diego's teams actually score, and which dimensions track winning.
5. **Examples** — the full methodology and a worked four‑year team analysis.

## The one rule that carries the whole architecture

Every advanced capability — simulation, log replay, unit tests, vision fusion, trajectory
optimization — attaches to a small number of structural **seams**. Build the seams correctly in week
one and each advanced feature becomes an *addition* at a known attachment point rather than a
*rewrite*. The spine of all of it: a per‑subsystem **IO layer**, with **no vendor type ever above
the IO line**.

---

*This site is generated from the `knowledge/` folder of the
[frc-code-scout](https://github.com/League-Robotics/frc-code-scout) repository, which also ships as
a Claude Code plugin with skills to **score** a team's code and **scaffold** this architecture into a
new robot project.*
