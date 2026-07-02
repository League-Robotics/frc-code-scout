---
title: "Lessons from Outside"
---

# Lessons from Outside

*What the broader robotics world treats as table stakes — and FRC mostly skips.*

The Elite Architecture was reconstructed from inside FRC. This closing section steps outside it. ROS,
Nav2, MoveIt, and the autonomous-driving stack converged on disciplines that FRC code rarely
adopts — graceful degradation, managed lifecycle, process isolation, spec-driven generation — and
seeing them named is the clearest way to see what the architecture is still missing.

It begins with a survey chapter and grows one lesson at a time: each deserves its own treatment, and
those are added here as they are written.

1. [Lessons from outside FRC](01-lessons-from-outside.md) — the outside-in view, and what it sets up.
2. [Spec-in, code-out — generators against the seam](02-code-generators.md) — RobotBuilder, Tuner X,
   YAGSL, and the LLM generators scored against the IO seam, and the one rule: generate the constants,
   own the architecture.
