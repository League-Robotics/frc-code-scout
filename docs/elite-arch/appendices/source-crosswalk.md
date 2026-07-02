---
title: Appendix C — Source-document crosswalk
weight: 3
---

**This appendix is the machine-checkable record that nothing in the source corpus was orphaned by the wiki rewrite.** Every document under `knowledge/` (and `docs/review/`) maps to the chapter or chapters that absorbed it, with one of three dispositions. **KEPT (reference)** — the file stays in place as a citable reference source, deeper than the wiki chapter that summarizes it. **ARCHIVED** — the file's content was fully absorbed into the wiki and the original moved to `knowledge/archived/`, where each archived file carries a header pointing back to the chapter that now owns it. **TOOL DEP** — the file stays in place because a skill or script reads it directly (scaffold-robot, analyze-team, setup-logging/simulation/testing, `build_site.py`, `agent_score.py`); it is load-bearing tooling, not just prose.

| Source document | Absorbed by | Disposition |
| --- | --- | --- |
| **build-spec/** | | |
| `elite-architecture.md` | [Part I](../part-1/) + [Part II](../part-2/) (ch. 1–23) | TOOL DEP — kept; source for scaffold-robot / analyze-team |
| `code-review-principles.md` | [Appendix D](reviewing-for-the-seams.md) | ARCHIVED |
| `logging.md` | [Part I ch. 7](../part-1/07-cross-cutting-practices.md) + [Part III ch. 29](../part-3/29-telemetry-replay-tests.md) | TOOL DEP — kept; source for setup-logging |
| `simulation.md` | [Part I ch. 7](../part-1/07-cross-cutting-practices.md) + [Part II](../part-2/) | TOOL DEP — kept; source for setup-simulation |
| `testing.md` | [Part I ch. 7](../part-1/07-cross-cutting-practices.md) + [Part II](../part-2/) | TOOL DEP — kept; source for setup-testing |
| `other-topics.md` | [Part I ch. 9 — Other advanced topics](../part-1/09-other-advanced-topics.md) | ARCHIVED |
| `subsystems/00–08` | [Part II ch. 18](../part-2/18-subsystem-archetypes.md) (and ch. 15–23) | KEPT (reference source) |
| **corpus-analysis/** | | |
| `02-frc-37-team-survey.md` | [Part I](../part-1/) + [Appendix A](how-we-developed-this/) | ARCHIVED |
| `03-io-layer-strategy-pattern.md` | [Part I ch. 3](../part-1/03-the-io-seam.md), [Part II ch. 16–17](../part-2/16-hardware-abstraction.md), [Appendix B](glossary.md) | ARCHIVED |
| `04-novice-to-elite-progression.md` | [Appendix A ch. 3 — maturity ladder](how-we-developed-this/03-the-maturity-ladder.md) | KEPT (reference) |
| `05-motor-io-interfaces.md` | [Part II ch. 17](../part-2/17-motor-interfaces.md), [Part III ch. 26](../part-3/26-portable-motor-interface.md) | KEPT (reference) |
| `06-lessons-from-broader-robotics.md` | [Lessons from Outside ch. 1](lessons-from-outside/01-lessons-from-outside.md) | ARCHIVED |
| `07-code-generators.md` | [Lessons from Outside ch. 2](lessons-from-outside/02-code-generators.md) | KEPT (reference) |
| `08-drivetrain-as-architecture.md` | [Part I ch. 6](../part-1/06-the-drivetrain.md), [Part II ch. 19](../part-2/19-the-drivetrain-subsystem.md), [Part III ch. 27](../part-3/27-portable-swerve-interface.md) | KEPT (reference) |
| **rubric/** | | |
| `rubric.md` | [Scoring — the rubric in full](../scoring/33-the-rubric.md) + [Appendix A ch. 2](how-we-developed-this/02-the-rubric.md) | TOOL DEP — kept; read by `build_site.py`, `agent_score.py`, scoring skills |
| **survey/** | | |
| `sd-frc-final-report.md` (+ inventories + `*.csv`) | [Scoring — the San Diego scoresheet](../scoring/34-the-san-diego-scoresheet.md) + [Appendix A ch. 4](how-we-developed-this/04-what-it-predicts.md) | KEPT (reference) |
| **examples/** | | |
| `methodology.md` | [Appendix A ch. 1](how-we-developed-this/01-reading-the-corpus.md) | KEPT (reference) |
| `patribots-four-year-scoring.md` | [Scoring — the Patribots, four years](../scoring/35-the-patribots-four-years.md) | KEPT (reference) |
| **alternatives/** | | |
| `01–04` + `README` | [Part I ch. 8](../part-1/08-alternatives.md), [Part II ch. 23](../part-2/23-coordination-graphs-trees.md) | KEPT (reference) |
| **specs/** | | |
| `portable-component-model.md` | [Part III ch. 25](../part-3/25-portable-component-model.md) (and ch. 24, 28–31), [Appendix B](glossary.md) | KEPT (reference) |
| `portable-motor-interface.md` | [Part III ch. 26](../part-3/26-portable-motor-interface.md) | KEPT (reference) |
| `portable-swerve-interface.md` | [Part III ch. 27](../part-3/27-portable-swerve-interface.md) | KEPT (reference) |
| **docs/review/** | | |
| `portable-component-model-review.md` | [Part III ch. 32](../part-3/32-open-questions.md) | KEPT (reference) |
