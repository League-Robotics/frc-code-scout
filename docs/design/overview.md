# FRC Code Scout — Overview

FRC Code Scout is an AI-agent-driven analysis and scaffolding tool for FIRST Robotics
Competition (and FTC) team software. It does two things:

1. **Score** — grade any team's published robot code against an 8-dimension
   sophistication rubric (D1 Hardware decoupling, D2 Coordination, D3 Simulation,
   D4 Testing, D5 Logging, D6 Auto/Path, D7 Vision/Localization, D8 Sustainability),
   derived from reading dozens of top teams' codebases and validated against a
   37-team national survey and a 24-team San Diego regional survey correlated with
   competition results (EPA).
2. **Build** — scaffold that same elite architecture (a per-subsystem IO layer,
   `RobotState`, and `Superstructure`, with no vendor type ever above the IO line)
   into new or existing WPILib robot projects, so teams can adopt the pattern
   directly instead of inferring it from a report.

The repo is driven by an AI coding agent (Claude Code, or any agent that reads
`AGENTS.md`) via a set of skills, and doubles as the source for a published Hugo
book/wiki ("Inside Competition Robot Code") that presents the rubric, the corpus
analysis, the build spec, the survey results, and worked examples.

**Primary users**: FRC/FTC mentors and students who want to know how their code
compares to the state of the art, and teams who want to build toward that
architecture directly.

**This document** exists to satisfy the CLASI `initialize` gate for an already
mature, working project. It is not a proposal — it describes what already exists.
