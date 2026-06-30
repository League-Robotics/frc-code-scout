---
title: 11. What the architecture predicts
weight: 11
---
A rubric is only worth trusting if its scores mean something. So the scores were tested: 24 San Diego
teams scored on the eight dimensions, each paired with season-matched Statbotics EPA (a normalized
strength rating built from match results), and the two correlated. The answer is honest rather than
triumphant.

## The headline: moderate, not decisive

Code sophistication correlates **moderately** with competition results — rubric total versus
normalized EPA is Spearman ρ ≈ 0.55. Better software is associated with better results, but it
explains only about a third of the variance. The per-dimension breakdown is the useful part:

| Dimension | vs normEPA | vs state %ile |
|---|---|---|
| D8 Sustainability | 0.60 | 0.62 |
| D6 Autonomous/Path | 0.59 | 0.60 |
| D7 Vision/Localization | 0.51 | 0.52 |
| D2 Coordination | 0.41 | 0.41 |
| D1 Architecture | 0.39 | 0.41 |
| D5 Logging | 0.35 | 0.36 |
| D4 Testing | 0.26 | 0.26 |
| D3 Simulation | 0.17 | 0.20 |

The split has a clean reading. D6 and D7 put points directly on the board — a team that runs real
autos and aligns to targets with vision scores more, immediately. D8 (CI, a carried library, docs, a
formatter) proxies overall program maturity, which sustains competitiveness across a season. D3 and
D4 — simulation and testing — are internal engineering investments whose payoff is robustness and
developer velocity, not raw match points; teams adopt them for reasons mostly orthogonal to a given
season's standings. (D4 is also near-constant — almost every team scores 0 — so its low correlation is
partly a low-variance artifact, not evidence that testing hurts.)

## The outliers carry the signal

Because the link is loose, the mismatches are where the lesson lives:

- **Sophisticated code, weak results — 3647 Millennium Falcons.** The most feature-complete codebase
  in San Diego (Σ = 20: maple-sim whole-robot simulation, AdvantageKit, 254-style architecture,
  multi-camera vision, Choreo, CI) finished in the bottom third of California in 2025. Their software
  is a model; that season's result was not.
- **Modest code, strong results — 4419 and 3749.** A minimal 14-file C++ repo (Σ = 5) paired with a
  top-quartile EPA. Whatever drove the result, it wasn't the software the rubric can see.
- **The aligned top — 4738 Patribots and 3128.** Patribots is the cleanest case of code and results
  agreeing: Σ = 19.5, a real AdvantageKit IO layer across every mechanism, and the best competition
  record in the set.

Code sophistication and competition performance are different axes. The rubric measures the first; it
does not pretend to measure the second.

## The confound, stated plainly

The most important caveat is that **most of what predicts EPA from "code" is size and program age, not
engineering quality.** A model of raw code features hits ρ ≈ 0.58 — but codebase size plus program
maturity *alone* scores ≈ 0.60, while the sophistication features with size removed score ≈ 0.38, and
a within-team view collapses to ≈ 0.05. Bigger, older, better-resourced programs have both more code
and better results. That D8 (program maturity) tops the dimension list is the same lurking variable
showing through. Do not read a high correlation as "good code wins," and do not reward sheer volume.

Other limits are real: n = 24 across mixed game years; shallow `.git`-stripped clones make D8 a floor;
EPA measures the whole robot and alliance context, not the software. A great controller can't
compensate for a slow intake or a no-show partner.

## What only the history could show

The validation across teams is a snapshot; the four-year deep dive on the Patribots is the
time-series. Re-cloned with full commit history and scored season by season, they show a clean
monotonic climb — Σ ≈ 5 → 10 → 17.5 → 20. The finding only the history could reveal: the leap to
elite-track scores happened **in the 2024 offseason, not in any build season.** The 2024 competition
robot ran on simple logging with no IO layer; the IO-layer/AdvantageKit rebuild landed in
July–August. That is [the "rewrite in the offseason" rule](10-the-maturity-ladder.md) showing up in a
real team's git log. The persistent gap across all four years, verified against every branch: not one
unit test has ever been written — which became the team's single highest-leverage next step.

The honest conclusion: the architecture is worth building because it makes a program *faster and more
durable*, and it modestly tracks results — but it is not a substitute for a good robot. The next
section turns from "is it true" to "how do you build it," starting with [the foundation-first
order](12-foundation-first.md).
